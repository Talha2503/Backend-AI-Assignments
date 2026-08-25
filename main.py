import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from database import init_db, get_connection
from supabase_client import supabase

from src.llm.schema import SupportRequest, SupportClassification
from src.llm.client import classify_with_llm, repair_with_llm
from src.llm.parser import parse_and_validate
from src.llm.quarantine import quarantine

from report_data import getReportData
from report_renderer import generate_pdf
from report_db import (
    init_report_db,
    create_report,
    update_report_path,
    get_report,
    get_todays_report,
)


security = HTTPBearer()


class TaskCreate(BaseModel):
    title: str | None = None
    done: bool = False


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ReportCreateRequest(BaseModel):
    force: bool = False


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        response = supabase.auth.get_user(credentials.credentials)

        if response.user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

        return response.user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


app = FastAPI(title="Task API", version="1.0")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    if request.url.path == "/support/classify":
        for error in exc.errors():
            location = error.get("loc", ())
            field = location[-1] if location else "request"

            return JSONResponse(
                status_code=400,
                content={
                    "message": f"Invalid field: {field}"
                }
            )

    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors()
        }
    )


# Initialize the existing PostgreSQL task database.
init_db()

# Initialize the SQLite reporting database.
init_report_db()


# ============================================================
# AUTH ENDPOINTS
# ============================================================

@app.post(
    "/auth/signup",
    status_code=201,
    summary="Sign up",
    description="Creates a new user account through Supabase Auth."
)
def signup(payload: SignupRequest):
    if not payload.email.strip() or not payload.password:
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
        })

        return response.user

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to create account"
        )


@app.post(
    "/auth/login",
    summary="Log in",
    description="Authenticates an existing user through Supabase Auth."
)
def login(payload: LoginRequest):
    if not payload.email.strip() or not payload.password:
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": response.user,
        }

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )


@app.post(
    "/auth/logout",
    status_code=204,
    summary="Log out",
    description="Logs out the authenticated user."
)
def logout(current_user=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
        return None

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Unable to log out"
        )


# ============================================================
# GENERAL ENDPOINTS
# ============================================================

@app.get(
    "/",
    summary="API info",
    description="Returns basic info about this API and its endpoints."
)
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": [
            "/auth/signup",
            "/auth/login",
            "/auth/logout",
            "/public/info",
            "/protected/profile",
            "/protected/dashboard",
            "/tasks",
            "/support/classify",
            "/reports",
            "/reports/{id}",
            "/reports/{id}/file",
        ],
    }


@app.get(
    "/health",
    summary="Health check",
    description="Confirms the server is alive."
)
def health():
    return {"status": "ok"}


@app.get(
    "/public/info",
    summary="Public information",
    description="Public endpoint that does not require authentication."
)
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }


@app.get(
    "/protected/profile",
    summary="Protected profile",
    description="Returns information about the authenticated user."
)
def protected_profile(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "created_at": current_user.created_at,
    }


@app.get(
    "/protected/dashboard",
    summary="Protected dashboard",
    description="Protected endpoint demonstrating reusable authentication."
)
def protected_dashboard(current_user=Depends(get_current_user)):
    return {
        "message": "Welcome to your protected dashboard!",
        "user_id": current_user.id,
        "email": current_user.email,
    }


# ============================================================
# TASK ENDPOINTS
# ============================================================

@app.get(
    "/tasks",
    summary="List all tasks",
    description="Returns every task currently stored in the database."
)
def list_tasks(current_user=Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title, done FROM tasks")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "title": r[1],
            "done": r[2]
        }
        for r in rows
    ]


@app.get(
    "/tasks/{task_id}",
    summary="Get one task",
    description="Returns a single task by id."
)
def get_task(
    task_id: int,
    current_user=Depends(get_current_user)
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, title, done FROM tasks WHERE id = %s",
        (task_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    description="Creates a new task."
)
def create_task(
    payload: TaskCreate,
    current_user=Depends(get_current_user)
):
    if not payload.title or not payload.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title is required and cannot be empty"
        )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id",
        (payload.title, payload.done),
    )

    new_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "id": new_id,
        "title": payload.title,
        "done": payload.done
    }


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    description="Updates an existing task."
)
def update_task(
    task_id: int,
    payload: TaskCreate,
    current_user=Depends(get_current_user)
):
    if not payload.title or not payload.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title is required and cannot be empty"
        )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s",
        (payload.title, payload.done, task_id),
    )

    updated = cur.rowcount

    conn.commit()

    if updated == 0:
        cur.close()
        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    cur.execute(
        "SELECT id, title, done FROM tasks WHERE id = %s",
        (task_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Removes a task permanently."
)
def delete_task(
    task_id: int,
    current_user=Depends(get_current_user)
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM tasks WHERE id = %s",
        (task_id,)
    )

    deleted = cur.rowcount

    conn.commit()

    cur.close()
    conn.close()

    if deleted == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return None


# ============================================================
# REPORT ENDPOINTS
# ============================================================

@app.post(
    "/reports",
    summary="Generate a report",
    description=(
        "Runs the complete reporting pipeline while preventing "
        "duplicate reports on the same day unless force=true "
        "is supplied."
    )
)
def create_report_endpoint(
    payload: ReportCreateRequest | None = None
):
    # Missing request body means force=false.
    force = payload.force if payload else False

    # 1. Check whether a report has already been generated today.
    if not force:
        existing_report = get_todays_report()

        if existing_report is not None:
            return JSONResponse(
                status_code=200,
                content={
                    "id": existing_report["id"],
                    "file": f"/reports/{existing_report['id']}/file",
                },
            )

    # 2. Query and aggregate the report data.
    report_data = getReportData()

    # 3. Create the report record first so we have its ID.
    created_at = datetime.now(timezone.utc).isoformat()

    report_id = create_report(created_at)

    # 4. Create the reports directory.
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 5. Generate a unique PDF path based on the report ID.
    file_path = reports_dir / f"{report_id}.pdf"

    try:
        # 6. Render HTML and generate the PDF.
        generate_pdf(
            report_data,
            str(file_path)
        )

    except Exception as exc:
        # Remove the bookkeeping row if PDF generation fails.
        from report_db import delete_report

        delete_report(report_id)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {type(exc).__name__}"
        )

    # 7. Store the generated PDF path.
    update_report_path(
        report_id,
        str(file_path)
    )

    # 8. Return the newly generated report.
    return JSONResponse(
        status_code=201,
        content={
            "id": report_id,
            "file": f"/reports/{report_id}/file",
        },
    )


@app.get(
    "/reports/{report_id}",
    summary="Get report metadata",
    description="Returns metadata and the download link for a generated report."
)
def get_report_endpoint(report_id: int):
    report = get_report(report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return {
        "id": report["id"],
        "path": report["path"],
        "created_at": report["created_at"],
        "file": f"/reports/{report_id}/file",
    }


@app.get(
    "/reports/{report_id}/file",
    summary="Download report PDF",
    description="Downloads the generated PDF report."
)
def get_report_file(report_id: int):
    report = get_report(report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    file_path = Path(report["path"])

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Report file not found"
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"report-{report_id}.pdf",
    )


# ============================================================
# LLM SUPPORT CLASSIFICATION
# ============================================================

@app.post(
    "/support/classify",
    response_model=SupportClassification,
    summary="Classify a support message",
    description="Classifies a support message using an LLM."
)
async def classify_support(payload: SupportRequest):

    # Production kill switch.
    if os.getenv("LLM_ENABLED", "true").lower() != "true":
        return {
            "category": "other",
            "urgency": "normal",
            "confidence": 0.5,
            "reason": "LLM classification is currently disabled."
        }

    # First model call.
    try:
        raw_output = classify_with_llm(payload.text)

    except Exception as exc:
        error_name = type(exc).__name__

        if error_name in {
            "APITimeoutError",
            "APIConnectionError",
        }:
            raise HTTPException(
                status_code=504,
                detail="LLM provider request timed out or could not be reached."
            )

        if hasattr(exc, "status_code"):
            status_code = exc.status_code

            if status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="LLM provider authentication failed."
                )

            if status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail="LLM provider rejected the request."
                )

        raise HTTPException(
            status_code=502,
            detail="LLM provider request failed."
        )

    # Parse and validate the first response.
    try:
        result = parse_and_validate(raw_output)
        return result

    except Exception as first_error:
        validation_error = str(first_error)

        # Exactly one repair attempt.
        try:
            repaired_output = repair_with_llm(
                text=payload.text,
                broken_output=raw_output,
                validation_error=validation_error,
            )

            repaired_result = parse_and_validate(
                repaired_output
            )

            return repaired_result

        except Exception as second_error:

            # Quarantine the failed model response.
            quarantine(
                input_text=payload.text,
                raw_output=raw_output,
                error=(
                    f"Initial error: {validation_error}; "
                    f"Repair error: {second_error}"
                ),
                prompt_version="support-v1",
            )

            raise HTTPException(
                status_code=422,
                detail=(
                    "LLM response could not be validated "
                    "after one repair attempt."
                )
            )