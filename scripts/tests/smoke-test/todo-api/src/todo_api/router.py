"""Todo API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/todos")
def list_todos():
    return []


@router.post("/todos")
def create_todo():
    return {"id": "1", "title": "sample"}


@router.patch("/todos/{todo_id}")
def update_todo(todo_id: str):
    return {"id": todo_id, "completed": True}


@router.delete("/todos/{todo_id}")
def delete_todo(todo_id: str):
    return None
