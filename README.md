# Task API

A CRUD API for managing a to-do list, built with FastAPI and backed by a PostgreSQL database running in Docker. Built as part of the FlyRank Backend AI Engineering internship — Week 2 (in-memory), Week 3 (SQLite), and this stage (containerized Postgres).

## What this is

A REST API that supports full CRUD (Create, Read, Update, Delete) on a list of tasks. Data is stored in a PostgreSQL database running in a Docker container, and the whole stack (app + database) starts with a single command.

## How to run it

1. Copy `.env.example` to `.env` (already set up for the compose stack, no changes needed for local dev)
2. Run:

docker compose up


That's it — this builds the app image, starts Postgres, waits for it to be healthy, then starts the API. The server is available at http://localhost:8000. Interactive Swagger docs are at http://localhost:8000/docs.

To stop everything: `docker compose down` (add `-v` to also wipe the database volume and start completely fresh).

## Environment variables

See `.env.example` for the required variable:

DATABASE_URL=postgres://postgres:dev@localhost:5432/tasks


Inside `compose.yaml`, the app actually connects to the database using the service name `db` instead of `localhost`, since containers on the same Docker network reach each other by service name, not `localhost`.

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

Postgres running in Docker, queried directly via `docker compose exec db psql -U postgres -d tasks`:

![Postgres data in psql](postgres-screenshot.png)

## Persistence, proven

Created a task via the API, then ran `docker compose down` followed by `docker compose up` — a full teardown and recreation of both containers. The task was still there afterward, because the named volume (`taskdata`) keeps the database files on disk independent of the containers' lifecycle. Containers are disposable; the volume isn't.

## The three storage swaps

| Stage | Where tasks live | Survives a restart? |
|---|---|---|
| Week 2 | a Python list in memory | No |
| Week 3 | a `tasks.db` SQLite file | Yes |
| This stage | rows in a Postgres container | Yes, and now it's a real database server, not just a file |

The API's endpoints, request/response shapes, and status codes never changed across any of these three swaps — only the storage layer underneath did. That separation is the actual lesson of this whole assignment sequence.

## AI vs me (Week 2, Stage 7)

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

## AI vs me (Stage 6, Week 3 — containerizing the stack)

**My prompt:**
> So for this assignment I used Docker Desktop, Postgres as the database. On startup it creates a table of 4 rows and its status is healthy.

**What the AI did better:**
Nothing, really — the prompt was thin enough that the AI had to guess at nearly everything, and most of its guesses skipped the exact parts of this assignment that mattered (secrets, persistence, startup ordering).

**What it got wrong or ignored:**
- Hardcoded the database password directly in the code instead of reading it from `.env` — exactly the secret-leak risk this assignment exists to prevent
- No volume on the `db` service — if the container is ever removed, all data is gone, which defeats the entire point of containerizing storage
- No healthcheck or `depends_on: condition: service_healthy` — this hits the exact startup race condition I ran into myself: the app can try to connect before Postgres is actually ready and crash
- No "only seed if empty" check — the 4 example rows would duplicate on every single restart
- `GET /tasks/{id}` builds its SQL with an f-string instead of a parameterized placeholder — a real injection risk
- `DELETE` returns `200` with a message body instead of `204` empty, breaking the status-code contract carried over from Assignments 1 and 2

**What my prompt forgot to specify — and what the AI silently decided:**
I never mentioned `.env`, secrets, volumes, a healthcheck, the seed-once rule, or parameterized queries at all — the AI filled in every one of those gaps with the least-safe option each time. My prompt also just said "creates a table of 4 rows," so it correctly saw 4 rows, but couldn't have known that count is meant to hold steady across restarts, not grow.

**One rematch:**
A better prompt would specify: "Containerize this FastAPI + Postgres CRUD API with Docker Compose. Read the database password from a `.env` file, never hardcode it. Use a named volume so data survives `docker compose down`. Add a Postgres healthcheck and make the app service wait for it. Seed 3 example tasks only if the table is empty. Keep all queries parameterized, and keep the exact same endpoints and status codes (400/404/204) as before." That single paragraph would have caught every issue above.