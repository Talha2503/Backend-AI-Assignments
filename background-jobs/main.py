import logging
import uuid

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel

import inngest
import inngest.fast_api


app = FastAPI()


# In-memory report storage.
reports = {}


# Create the Inngest client.
inngest_client = inngest.Inngest(
    app_id="report-api",
    logger=logging.getLogger("uvicorn"),
)


# Request model for creating reports.
class ReportRequest(BaseModel):
    topic: str


# -----------------------------
# Stage 1: Say Hello
# -----------------------------

@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(
        event="test/hello"
    ),
)
async def say_hello(ctx: inngest.Context) -> str:
    await ctx.step.sleep(
        "wait-5-seconds",
        5,
    )

    return "Hello from the background!"


# -----------------------------
# Stage 2 + Stage 3: Make Report
# -----------------------------

@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(
        event="report/requested"
    ),
    retries=2,
)
async def make_report(ctx: inngest.Context):
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    # Simulate the slow report-generation work.
    await ctx.step.sleep(
        "do-the-slow-work",
        8,
    )

    # Build the report and save it.
    def build_report():
        # Stage 3: intentionally fail this job to demonstrate retries.
        if topic == "fail":
            raise RuntimeError("The report oven is broken!")

        result = {
            "summary": f"Report generated for topic: {topic}",
            "topic": topic,
        }

        reports[report_id] = {
            "id": report_id,
            "topic": topic,
            "status": "done",
            "result": result,
        }

        return result

    return await ctx.step.run(
        "build-report",
        build_report,
    )


# -----------------------------
# Serve Inngest
# -----------------------------

inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello, make_report],
)


# -----------------------------
# Health
# -----------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------------
# Create Report
# -----------------------------

@app.post("/reports", status_code=status.HTTP_202_ACCEPTED)
async def create_report(request: Request):
    body = await request.json()

    # Reject missing topic at the door.
    if not body.get("topic"):
        raise HTTPException(
            status_code=400,
            detail="topic is required",
        )

    topic = body["topic"]

    report_id = str(uuid.uuid4())

    reports[report_id] = {
        "id": report_id,
        "topic": topic,
        "status": "pending",
    }

    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "id": report_id,
                "topic": topic,
            },
        )
    )

    return {
        "id": report_id,
        "status": "pending",
    }


# -----------------------------
# Report Status
# -----------------------------

@app.get("/reports/{report_id}")
def get_report(report_id: str):
    report = reports.get(report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report