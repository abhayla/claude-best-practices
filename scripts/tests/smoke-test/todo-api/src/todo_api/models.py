"""Database models for Todo API."""


class User:
    id: str
    email: str
    password_hash: str


class Todo:
    id: str
    title: str
    description: str
    completed: bool
    user_id: str
