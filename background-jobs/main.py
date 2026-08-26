import logging

from fastapi import FastAPI

import inngest
import inngest.fast_api


app = FastAPI()


# Create the Inngest client.
inngest_client = inngest.Inngest(
    app_id="report-api",
    logger=logging.getLogger("uvicorn"),
)


# Create the first background function.
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


# Serve Inngest functions at /api/inngest.
inngest.fast_api.serve(
    app,
    inngest_client,
    [say_hello],
)


@app.get("/health")
def health():
    return {"status": "ok"}