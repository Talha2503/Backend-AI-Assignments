markdown
# Task API

A small CRUD API for managing a to-do list, built with FastAPI and backed by a SQLite database. Built as part of the FlyRank Backend AI Engineering internship — Week 2 (in-memory) and Week 3 (SQLite persistence).

## What this is

A REST API that supports full CRUD (Create, Read, Update, Delete) on a list of tasks. Data is stored in a SQLite database (`tasks.db`) and survives server restarts.

## Why SQLite

SQLite needs no separate server or installation — the whole database is a single file. That makes it perfect for a small project like this: zero setup, and the data still survives a restart, which is the whole point of this stage. For a larger production app I'd reach for Postgres, but the API layer wouldn't need to change at all to get there.

## Where the database lives

`tasks.db`, created automatically in the project folder the first time the app runs. It's git-ignored, so each fresh clone starts with its own empty database and reseeds the 3 example tasks on first run.

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
content-type: application/json

{"id":4,"title":"Buy milk","done":false}


## Database

Opened in DB Browser for SQLite, showing the `tasks` table:

![DB Browser showing the tasks table](db-browser-screenshot.png)

Example query run by hand in Stage 4:

```sql
DELETE FROM tasks WHERE done = 1;
```

This removed all 3 seeded tasks, and the very next `GET /tasks` call showed the table empty — then reseeded automatically on the next restart, since seeding only happens when the table is empty.

## Swagger UI

![Swagger UI showing all endpoints](swagger-screenshot.png)

Full CRUD cycle tested via "Try it out":

| Step | Screenshot |
|---|---|
| Create task — request | `swagger-create-task-1.png` |
| Create task — 201 response | `swagger-create-task-2.png` |
| List tasks — request | `swagger-get-tasks-1.png` |
| List tasks — response (new task visible) | `swagger-get-tasks-2.png` |

## The mortality experiment (Week 2)

In the original in-memory version, restarting the server reset tasks back to the 3 seed tasks — anything created, updated, or deleted was lost. Week 3 fixed exactly this by moving storage to SQLite: now the database file on disk is the source of truth, not the running program's memory.

## AI vs me (Stage 7, Week 2)

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

## AI vs me (Stage 6, Week 3 — the database migration)

**My prompt:**
> So what I did was store a database in the CRUD that was empty before, that's it.

**What the AI did better:**
Nothing, really — my prompt was extremely thin, so the AI had to guess at almost everything, and most of its guesses were wrong or unsafe. If anything, this run proved how much a vague prompt costs you.

**What it got wrong or ignored:**
- The seed data duplicates every time the server restarts — no "only insert if the table is empty" check, so 3 tasks became 6 after a single restart
- `GET /tasks/{id}` builds the SQL query with an f-string (`WHERE id = {task_id}`) instead of a parameterized `?` placeholder — a real SQL injection risk, not just a style issue
- `PUT` and `DELETE` never check whether a row actually existed before responding — updating or deleting a nonexistent id still returns `200`, never `404`
- Missing `title` returns FastAPI's default `422` instead of the `400` my original API used
- `done` comes back as `0`/`1` instead of `true`/`false`, breaking the "the API doesn't change" promise from Assignment 1
- `DELETE` returns `200` with a message body instead of `204` with an empty body

**What my prompt forgot to specify — and what the AI silently decided:**
Almost everything. I never said which database to use (it guessed SQLite, correctly, but that was luck), never mentioned seeding at all, never said to reuse parameterized queries, and never restated the 400/404/204 status code rules from Assignment 1. The AI filled every one of those gaps with its own defaults, and most of those defaults were either insecure or wrong.

**One rematch:**
A much better prompt would specify: "Migrate this in-memory FastAPI CRUD API to SQLite. Use parameterized queries only. Seed 3 example tasks, but only if the table is empty — never duplicate them on restart. Keep the exact same endpoints, status codes (400 for invalid input, 404 for unknown id, 204 for delete), and response shapes as before." That single paragraph would have caught nearly every bug above.

**What my prompt forgot to specify — and what the AI silently decided:**
I never specified the seed data, the health check endpoint, the exact status codes (400 vs 422, 204 vs 200), or that empty-string titles should be rejected too. The AI just picked its own defaults for all of that — mostly FastAPI's out-of-the-box validation behavior — instead of the exact rules the assignment wanted.

**One rematch:**
Adding "reject empty-string titles with 400, return 204 with no body on delete, and include GET / and GET /health" to my prompt would fix most of these gaps in one pass.
