# Task API

A secure REST API built with FastAPI, PostgreSQL, Docker, and Supabase Authentication. The project provides task CRUD operations, user signup/login/logout, JWT-based authentication, protected routes, reusable authentication middleware, and interactive Swagger documentation.

Built as part of the FlyRank Backend AI Engineering internship.

## What this is

Task API is a backend service for managing a to-do list.

The project includes:

* FastAPI REST API
* PostgreSQL database running in Docker
* Supabase Authentication
* User signup and login
* JWT access-token authentication
* Reusable authentication dependency for protected routes
* Protected task endpoints
* Public and protected example routes
* Logout endpoint
* Swagger UI with Bearer JWT authentication
* Persistent PostgreSQL storage using a Docker volume

## Features

### Authentication

* `POST /auth/signup` — Create a new Supabase user
* `POST /auth/login` — Authenticate a user and receive access/refresh tokens
* `POST /auth/logout` — Log out an authenticated user

### Protected routes

* `GET /protected/profile` — Returns authenticated user information
* `GET /protected/dashboard` — Example protected route
* All `/tasks` endpoints require a valid Supabase access token

### Public routes

* `GET /` — API information
* `GET /health` — Health check
* `GET /public/info` — Public information endpoint

## How to run it

### 1. Configure environment variables

Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

Add your own Supabase credentials to `.env`.

Never commit `.env` to GitHub.

The repository includes `.env.example` as a safe template containing placeholder values.

### 2. Start the application

Run:

```bash
docker compose up --build
```

This builds the API image, starts PostgreSQL, waits for the database to become healthy, and starts the FastAPI server.

The API will be available at:

`http://localhost:8000`

Interactive Swagger documentation is available at:

`http://localhost:8000/docs`

To stop the application:

```bash
docker compose down
```

To remove the database volume and start completely fresh:

```bash
docker compose down -v
```

## Environment variables

The application uses environment variables for configuration and secrets.

See `.env.example` for the required variable names.

Example:

```env
DATABASE_URL=postgres://postgres:dev@db:5432/tasks
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Do not put real Supabase credentials in the README, source code, or GitHub repository.

The `.env` file is included in `.gitignore`.

## API Reference

| Method | Endpoint               | Description                        | Authentication | Success | Errors        |
| ------ | ---------------------- | ---------------------------------- | -------------- | ------- | ------------- |
| POST   | `/auth/signup`         | Create a new user                  | No             | 201     | 400           |
| POST   | `/auth/login`          | Log in and receive JWT tokens      | No             | 200     | 400, 401      |
| POST   | `/auth/logout`         | Log out the current user           | Yes            | 204     | 401           |
| GET    | `/public/info`         | Public information                 | No             | 200     | —             |
| GET    | `/protected/profile`   | Get authenticated user information | Yes            | 200     | 401           |
| GET    | `/protected/dashboard` | Protected dashboard example        | Yes            | 200     | 401           |
| GET    | `/`                    | API information                    | No             | 200     | —             |
| GET    | `/health`              | Health check                       | No             | 200     | —             |
| GET    | `/tasks`               | List all tasks                     | Yes            | 200     | 401           |
| GET    | `/tasks/{id}`          | Get one task                       | Yes            | 200     | 401, 404      |
| POST   | `/tasks`               | Create a task                      | Yes            | 201     | 400, 401      |
| PUT    | `/tasks/{id}`          | Update a task                      | Yes            | 200     | 400, 401, 404 |
| DELETE | `/tasks/{id}`          | Delete a task                      | Yes            | 204     | 401, 404      |

## Authentication flow

### 1. Sign up

Send an email and password to:

```text
POST /auth/signup
```

Example:

```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

A successful request returns `201 Created` and the Supabase user object.

### 2. Log in

Send the same credentials to:

```text
POST /auth/login
```

A successful request returns `200 OK` together with an access token and refresh token.

The access token is a JWT and is used to access protected endpoints.

### 3. Authorize protected routes

In Swagger UI, click the **Authorize** button and enter:

```text
Bearer YOUR_ACCESS_TOKEN
```

After authorization, Swagger can send the JWT automatically to protected endpoints.

## Protected routes

The application uses FastAPI's `HTTPBearer` security scheme and a reusable authentication dependency.

The authentication dependency:

1. Extracts the Bearer token from the `Authorization` header.
2. Sends the token to Supabase for verification.
3. Rejects missing, invalid, expired, or tampered tokens with `401 Unauthorized`.
4. Makes the authenticated Supabase user available to protected routes.

This authentication dependency is reused by the protected endpoints instead of duplicating token-verification logic.

## Swagger UI

Interactive API documentation is available at:

`http://localhost:8000/docs`

Swagger provides an **Authorize** button for entering a JWT once and reusing it when testing protected endpoints.

The protected routes display lock icons in Swagger.

### Swagger authentication

![Swagger UI with Bearer authentication](swagger-authenticated.PNG)

### Protected routes

![Protected routes with Bearer authentication](swagger-protected-routes.PNG)

## Example authenticated request

After logging in and obtaining an access token:

```bash
curl -i -X GET http://localhost:8000/protected/profile \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

A valid token returns `200 OK`.

An invalid or expired token returns `401 Unauthorized`.

## Database

PostgreSQL runs inside Docker and is accessed by the FastAPI application through the Docker Compose network.

The database uses a named Docker volume so task data survives container restarts.

PostgreSQL can be accessed with:

```bash
docker compose exec db psql -U postgres -d tasks
```

![Postgres data in psql](postgres-screenshot.png)

## Persistence

Task data persists even when the Docker containers are stopped and recreated because PostgreSQL stores its data in a named Docker volume.

The API can therefore be stopped with:

```bash
docker compose down
```

and started again with:

```bash
docker compose up
```

without losing the stored tasks.

## Project structure

```text
task-api/
├── main.py
├── database.py
├── supabase_client.py
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── .env.example
├── .gitignore
├── README.md
├── swagger-authenticated.PNG
├── swagger-protected-routes.PNG
└── screenshots/
```

## Security

Secrets are kept outside the source code.

* `.env` is ignored by Git.
* `.env.example` contains only placeholder values.
* Supabase authentication is handled by Supabase Auth.
* JWTs are verified through Supabase before protected routes execute.
* Protected routes reject missing or invalid credentials.
* Database queries use parameterized SQL queries.

Never commit real Supabase credentials or access tokens to GitHub.

## GitHub

The project is publicly available on GitHub:

https://github.com/Talha2503/Backend-AI-Assignments

The repository contains the project source code and the completed authentication stages.

## Project stages

| Stage   | Description                          | Status      |
| ------- | ------------------------------------ | ----------- |
| Stage 1 | Signup and Login                     | Complete    |
| Stage 2 | Public and Protected Routes          | Complete    |
| Stage 3 | Token Verification                   | Complete    |
| Stage 4 | Authentication Middleware and Logout | Complete    |
| Stage 5 | Swagger UI Bearer Authentication     | Complete    |
| Stage 6 | GitHub Publication and README        | In progress |
| Stage 7 | AI vs Me — Bonus                     | Optional    |

## Earlier storage stages

| Stage           | Storage               | Persistence |
| --------------- | --------------------- | ----------- |
| Week 2          | Python in-memory list | No          |
| Week 3          | SQLite                | Yes         |
| Current project | PostgreSQL in Docker  | Yes         |

The API contract remains consistent while the underlying storage layer evolves.

The LLM provider can run locally or in a datacentre because the application uses only LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL to configure it.

## LLM Support Classification

### Valid request

curl -X POST http://127.0.0.1:8000/support/classify -H "Content-Type: application/json" -d "{\"text\":\"I was charged twice for my subscription\"}"
## License

### Deliberately Broken request

curl -X POST http://127.0.0.1:8000/support/classify -H "Content-Type: application/json" -d "{}"

### LICENSE

This project was created for educational purposes as part of the FlyRank Backend AI Engineering internship.


