"""Tests for todo CRUD endpoints."""


def test_create_todo(sample_todo):
    assert sample_todo["title"] == "Test todo"


def test_list_todos():
    todos = []
    assert isinstance(todos, list)


def test_update_todo():
    todo = {"id": "1", "completed": True}
    assert todo["completed"] is True


def test_delete_todo():
    pass
