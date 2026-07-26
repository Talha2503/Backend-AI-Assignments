from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str | None = None
    done: bool = False


app = FastAPI(title="Task API", version="1.0")

# In-memory "database" -- a plain Python list.
# Resets every time the server restarts (that's Week 3's lesson).
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Finish assignment", "done": False},
    {"id": 3, "title": "Walk the dog", "done": True},
]
next_id = 4


@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    global next_id
    # The server never trusts the client -- reject empty/missing titles.
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="Title is required and cannot be empty")

    task = {"id": next_id, "title": payload.title, "done": payload.done}
    tasks.append(task)
    next_id += 1
    return task
