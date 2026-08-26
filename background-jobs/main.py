import logging
import uuid

from fastapi import FastAPI, HTTPException, status
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


# Stage 1 background function.
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


# Stage 2 background report function.
@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(
        event="report/requested"
    ),
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


# Serve all Inngest functions.
inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello, make_report],
)


# Health endpoint.
@app.get("/health")
def health():
    return {"status": "ok"}


# Create a report.
@app.post("/reports", status_code=status.HTTP_202_ACCEPTED)
async def create_report(request: ReportRequest):
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


# Check report status.
@app.get("/reports/{report_id}")
def get_report(report_id: str):
    report = reports.get(report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report