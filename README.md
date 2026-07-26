# Task API

A small in-memory CRUD API for managing a to-do list, built with **FastAPI**.
Built as part of the FlyRank Backend AI Engineering internship, Week 2 assignment.

## What this is

A REST API that supports full CRUD (Create, Read, Update, Delete) on a list of tasks.
Data is stored **in memory** — it resets every time the server restarts. There is no
database yet (that's next week).

## How to run it

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The server starts on **http://localhost:8000**.

Interactive Swagger docs are available at **http://localhost:8000/docs**.

## Endpoints

| Method | Path            | Description                          | Success | Errors        |
|--------|-----------------|---------------------------------------|---------|----------------|
| GET    | `/`             | API info                              | 200     | —              |
| GET    | `/health`       | Health check                          | 200     | —              |
| GET    | `/tasks`        | List all tasks                        | 200     | —              |
| GET    | `/tasks/{id}`   | Get one task                          | 200     | 404            |
| POST   | `/tasks`        | Create a task                         | 201     | 400            |
| PUT    | `/tasks/{id}`   | Update a task's title/done            | 200     | 400, 404       |
| DELETE | `/tasks/{id}`   | Delete a task                         | 204     | 404            |

## Example request

```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
```

```
HTTP/1.1 201 Created
date: Sun, 26 Jul 2026 02:51:44 GMT
server: uvicorn
content-length: 40
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Swagger UI

![Swagger UI showing all endpoints](swagger-screenshot.png)

*(Add your own screenshot here after running `/docs` locally and taking a screenshot
of the full endpoint list with "Try it out" expanded.)*

## The mortality experiment

Restarting the server resets `tasks` back to the 3 seed tasks — anything created,
updated, or deleted during the previous run is gone. This is because the list lives
only in the Python process's memory; nothing is written to disk. This is the exact
problem a database solves, which is why Week 3 exists.

## AI vs me

*(To be completed in Stage 7 — bonus.)*
