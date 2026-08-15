from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import init_db, get_connection


class TaskCreate(BaseModel):
    title: str | None = None
    done: bool = False


app = FastAPI(title="Task API", version="1.0")
init_db()


@app.get("/", summary="API info", description="Returns basic info about this API and its endpoints.")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", summary="Health check", description="Confirms the server is alive. Used by monitoring tools.")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="List all tasks", description="Returns every task currently stored in the database.")
def list_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "title": r[1], "done": r[2]} for r in rows]


@app.get("/tasks/{task_id}", summary="Get one task", description="Returns a single task by id, or 404 if it doesn't exist.")
def get_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"id": row[0], "title": row[1], "done": row[2]}


@app.post("/tasks", status_code=201, summary="Create a task", description="Creates a new task. Title is required and cannot be empty.")
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (payload.title, int(payload.done)),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {"id": new_id, "title": payload.title, "done": payload.done}


@app.put("/tasks/{task_id}", summary="Update a task", description="Replaces a task's title and done status. 404 if the task doesn't exist.")
def update_task(task_id: int, payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")

    conn = get_connection()
    cursor = conn.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (payload.title, int(payload.done), task_id),
    )
    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row_to_task(row)


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task", description="Removes a task permanently. 404 if it doesn't exist.")
def delete_task(task_id: int):
    conn = get_connection()
    cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")