# Background Jobs API

## What This Is

This project demonstrates a professional background-job pattern using **FastAPI, Python, Inngest, and an in-memory report store**. The API accepts report requests immediately with HTTP `202 Accepted`, while the slow report generation happens in the background. Clients can poll the status endpoint until the report is completed. The project also demonstrates automatic retries for failed background jobs and a cron-triggered heartbeat that runs independently of HTTP requests.

## Project Structure

```text
background-jobs/
├── main.py
├── requirements.txt
├── Inngest Server Screenshot.PNG
├── Inngest Server Screenshot 2.PNG
├── Inngest Server Secreenshot 3.PNG
├── Inngest Server Screenshot 4.PNG
├── Inngest Server Screenshot 5.PNG
├── Inngest Server Screenshot 6.PNG
└── Inngest Server Screenshot 7.PNG
```

## Requirements

* Python
* FastAPI
* Uvicorn
* Inngest Python SDK
* Node.js / npm for the Inngest Dev Server

## How to Run

### Terminal 1 — Start the API

From the `background-jobs` directory:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

### Terminal 2 — Start the Inngest Dev Server

From the `background-jobs` directory:

```bash
npx inngest-cli@latest dev -u http://localhost:8000/api/inngest
```

The Inngest dashboard will be available at:

```text
http://localhost:8288
```

Both terminals must remain running while testing the background jobs and cron function.

## API Endpoints

| Method | Endpoint        | Description                                                     |
| ------ | --------------- | --------------------------------------------------------------- |
| GET    | `/health`       | Returns the API health status                                   |
| POST   | `/reports`      | Accepts a report request and returns `202 Accepted` immediately |
| GET    | `/reports/{id}` | Returns the current status and result of a report               |

### Example Request

```bash
curl -i -X POST http://localhost:8000/reports -H "Content-Type: application/json" -d "{\"topic\":\"cats\"}"
```

The API responds immediately with:

```text
HTTP/1.1 202 Accepted

{"id":"e8362447-a608-43c3-97d5-4420a3266dd8","status":"pending"}
```

The report is then processed by Inngest in the background.

## Inngest Functions

| Function      | Trigger            | Purpose                                                                 |
| ------------- | ------------------ | ----------------------------------------------------------------------- |
| `say-hello`   | `test/hello`       | Demonstrates a basic background function with a 5-second sleep          |
| `make-report` | `report/requested` | Performs the simulated 8-second report generation and stores the result |
| `heartbeat`   | `* * * * *`        | Runs every minute and logs pending, done, and failed report counts      |

## Background Job Proof

A report request returns immediately with `202 Accepted`:

```text
HTTP/1.1 202 Accepted

{"id":"e8362447-a608-43c3-97d5-4420a3266dd8","status":"pending"}
```

Polling with an incorrect or unknown ID returns:

```text
HTTP/1.1 404 Not Found

{"detail":"Report not found"}
```

Polling the correct report ID after the background job completes returns:

```text
HTTP/1.1 200 OK

{"id":"e8362447-a608-43c3-97d5-4420a3266dd8","topic":"cats","status":"done","result":{"summary":"Report generated for topic: cats","topic":"cats"}}
```

This demonstrates the core background-job pattern: **accept the request quickly, perform the slow work in the background, and allow the client to poll for the result.**

## Stage 3 — Retries and Validation

A temporary failure such as the `fail` topic is retried automatically by Inngest, while invalid input such as a missing topic is rejected immediately with `400` because bad input should not create a background job.

## Stage 4 — Cron Heartbeat

The cron expression `0 8 * * *` runs the heartbeat every day at 08:00.

The cron expression `0 22 * * 0` runs the heartbeat every Sunday at 22:00.

The heartbeat itself uses `* * * * *` during testing, which runs once every minute.

## Retry Demonstration

The `make-report` function is configured with two retries. When the topic is `fail`, the report function raises:

```text
The report oven is broken!
```

Inngest automatically retries the failed function, resulting in three total attempts before the run is marked as failed.

## Cron Demonstration

The `heartbeat` function is triggered by the clock rather than an HTTP request or event. It counts reports in the in-memory store and logs:

```text
Heartbeat: pending=0, done=1, failed=1
```

During testing, the Inngest dashboard showed two completed heartbeat runs approximately one minute apart.

## Dashboard Proof

The Inngest Dev Server dashboard shows the three registered functions and their triggers:

* `heartbeat` — `* * * * *`
* `make-report` — `report/requested`
* `say-hello` — `test/hello`

It also shows completed heartbeat runs and the failed `make-report` run demonstrating automatic retries.

![Inngest Dashboard Runs](Inngest%20Server%20Screenshot%207.PNG)

## Key Concepts Demonstrated

* HTTP `202 Accepted`
* Background processing
* Event-driven jobs
* Inngest functions
* Polling
* Eventual consistency
* Automatic retries
* Retry backoff
* Input validation
* Cron scheduling
* In-memory job state
* FastAPI
* Public GitHub deployment/documentation

## Repository

This assignment is part of the `Backend-AI-Assignments` repository and is located in the `background-jobs/` folder.
