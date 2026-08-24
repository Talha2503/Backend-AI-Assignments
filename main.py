from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from database import init_db, get_connection
from supabase_client import supabase


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

init_db()


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
            "/tasks"
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