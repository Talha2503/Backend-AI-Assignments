import logging
import uuid

from fastapi import FastAPI, HTTPException
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
    topic: str | None = None


# Stage 1: First background function.
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


# Stage 2/3: Background report function.
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

    # Simulate slow work.
    await ctx.step.sleep(
        "do-the-slow-work",
        8,
    )

    # Build and save the report.
    async def build_report():
        if topic == "fail":
            raise Exception("The report oven is broken!")

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


# Stage 4: Cron heartbeat.
@inngest_client.create_function(
    fn_id="heartbeat",
    trigger=inngest.TriggerCron(
        cron="* * * * *"
    ),
)
async def heartbeat(ctx: inngest.Context):
    pending = sum(
        1 for report in reports.values()
        if report["status"] == "pending"
    )

    done = sum(
        1 for report in reports.values()
        if report["status"] == "done"
    )

    failed = sum(
        1 for report in reports.values()
        if report["status"] == "failed"
    )

    message = (
        f"Heartbeat: pending={pending}, "
        f"done={done}, failed={failed}"
    )

    print(message)

    return {
        "pending": pending,
        "done": done,
        "failed": failed,
    }


# Serve all Inngest functions at /api/inngest.
inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello, make_report, heartbeat],
)


# Health check.
@app.get("/health")
def health():
    return {"status": "ok"}


# Create a report.
@app.post("/reports", status_code=202)
async def create_report(request: ReportRequest):
    if not request.topic:
        raise HTTPException(
            status_code=400,
            detail="Topic is required",
        )

    report_id = str(uuid.uuid4())

    reports[report_id] = {
        "id": report_id,
        "topic": request.topic,
        "status": "pending",
    }

    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "id": report_id,
                "topic": request.topic,
            },
        )
    )

    return {
        "id": report_id,
        "status": "pending",
    }


# Get report status.
@app.get("/reports/{report_id}")
def get_report(report_id: str):
    report = reports.get(report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report