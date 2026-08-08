from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import init_db, get_connection


class TaskCreate(BaseModel):
    title: str | None = None
    done: bool = False


app = FastAPI(title="Task API", version="1.0")
init_db()

# In-memory "database" -- a plain Python list.
# Still used by POST/PUT/DELETE for now -- Stages 2-3 move these to SQL too.
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Finish assignment", "done": False},
    {"id": 3, "title": "Walk the dog", "done": True},
]
next_id = 4


def row_to_task(row):
    """Convert a sqlite3.Row into a plain dict with a real bool for `done`."""
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


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
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [row_to_task(row) for row in rows]


@app.get("/tasks/{task_id}", summary="Get one task", description="Returns a single task by id, or 404 if it doesn't exist.")
def get_task(task_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return row_to_task(row)


@app.post("/tasks", status_code=201, summary="Create a task", description="Creates a new task. Title is required and cannot be empty.")
def create_task(payload: TaskCreate):
    global next_id
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")

    task = {"id": next_id, "title": payload.title, "done": payload.done}
    tasks.append(task)
    next_id += 1
    return task


@app.put("/tasks/{task_id}", summary="Update a task", description="Replaces a task's title and done status. 404 if the task doesn't exist.")
def update_task(task_id: int, payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")

    for task in tasks:
        if task["id"] == task_id:
            task["title"] = payload.title
            task["done"] = payload.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task", description="Removes a task permanently. 404 if it doesn't exist.")
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")