import psycopg2
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


def get_db():
    conn = psycopg2.connect(
        host="db",
        database="tasks",
        user="postgres",
        password="dev"
    )
    return conn


def setup():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            done BOOLEAN
        )
    """)
    # insert 4 example rows
    cur.execute("INSERT INTO tasks (title, done) VALUES ('Buy groceries', false)")
    cur.execute("INSERT INTO tasks (title, done) VALUES ('Finish assignment', false)")
    cur.execute("INSERT INTO tasks (title, done) VALUES ('Walk the dog', true)")
    cur.execute("INSERT INTO tasks (title, done) VALUES ('Buy milk', false)")
    conn.commit()
    cur.close()
    conn.close()


setup()


class Task(BaseModel):
    title: str
    done: bool = False


@app.get("/tasks")
def get_tasks():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "done": r[2]} for r in rows]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM tasks WHERE id = {task_id}")
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"id": row[0], "title": row[1], "done": row[2]}


@app.post("/tasks")
def create_task(task: Task):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id", (task.title, task.done))
    new_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": new_id, "title": task.title, "done": task.done}


@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: Task):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET title = %s, done = %s WHERE id = %s", (task.title, task.done, task_id))
    conn.commit()
    conn.close()
    return {"id": task_id, "title": task.title, "done": task.done}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    conn.commit()
    conn.close()
    return {"message": "deleted"}