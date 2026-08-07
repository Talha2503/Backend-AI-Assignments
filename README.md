# Task API

A small in-memory CRUD API for managing a to-do list, built with FastAPI. Built as part of the FlyRank Backend AI Engineering internship, Week 2 assignment.

## What this is

A REST API that supports full CRUD (Create, Read, Update, Delete) on a list of tasks. Data is stored in memory — it resets every time the server restarts. There is no database yet (that's next week).

## How to run it

pip install -r requirements.txt
uvicorn main:app --reload


The server starts on http://localhost:8000.
Interactive Swagger docs are available at http://localhost:8000/docs.

## Endpoints

| Method | Path | Description | Success | Errors |
|---|---|---|---|---|
| GET | / | API info | 200 | — |
| GET | /health | Health check | 200 | — |
| GET | /tasks | List all tasks | 200 | — |
| GET | /tasks/{id} | Get one task | 200 | 404 |
| POST | /tasks | Create a task | 201 | 400 |
| PUT | /tasks/{id} | Update a task's title/done | 200 | 400, 404 |
| DELETE | /tasks/{id} | Delete a task | 204 | 404 |

## Example request

curl -i -X POST http://localhost:8000/tasks
-H "Content-Type: application/json"
-d '{"title":"Buy milk"}'

HTTP/1.1 201 Created
date: Sun, 26 Jul 2026 02:51:44 GMT
server: uvicorn
content-length: 40
content-type: application/json

{"id":4,"title":"Buy milk","done":false}


## Swagger UI

![Swagger UI showing all endpoints](swagger-screenshot.png)

Full CRUD cycle tested via "Try it out":

| Step | Screenshot |
|---|---|
| Create task — request | `swagger-create-task-1.png` |
| Create task — 201 response | `swagger-create-task-2.png` |
| List tasks — request | `swagger-get-tasks-1.png` |
| List tasks — response (new task visible) | `swagger-get-tasks-2.png` |

## The mortality experiment

Restarting the server resets tasks back to the 3 seed tasks — anything created, updated, or deleted during the previous run is gone. This is because the list lives only in the Python process's memory; nothing is written to disk. This is the exact problem a database solves, which is why Week 3 exists.

## AI vs me (Stage 7)

**My prompt:**
> A small in-memory CRUD API for managing a to-do list, built with FastAPI. Built as part of the FlyRank Backend AI Engineering internship, Week 2 assignment. A REST API that supports full CRUD (Create, Read, Update, Delete) on a list of tasks. Data is stored in memory — it resets every time the server restarts. There is no database yet.

**What the AI did better:**
Honestly, not much — the core CRUD logic (loop over the list, match by id) is basically identical to mine, since there's only one obvious way to write it. I understand its version fully; it's simpler than mine because it skips validation detail.

**What it got wrong or ignored:**
- No `GET /` or `/health` endpoints — I never mentioned them in my prompt, so it had no way to know
- Didn't seed the 3 example tasks — starts with an empty list
- Missing `title` returns FastAPI's default `422` error instead of the `400` the assignment requires
- Accepts an empty string `""` as a valid title (no `.strip()` check) — mine rejects it
- `DELETE` returns `200` with a message body instead of `204` with an empty body

**What my prompt forgot to specify — and what the AI silently decided:**
I never specified the seed data, the health check endpoint, the exact status codes (400 vs 422, 204 vs 200), or that empty-string titles should be rejected too. The AI just picked its own defaults for all of that — mostly FastAPI's out-of-the-box validation behavior — instead of the exact rules the assignment wanted.

**One rematch:**
Adding "reject empty-string titles with 400, return 204 with no body on delete, and include GET / and GET /health" to my prompt would fix most of these gaps in one pass.
