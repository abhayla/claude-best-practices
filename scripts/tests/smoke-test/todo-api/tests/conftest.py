"""Shared test fixtures for Todo API tests."""

import pytest


@pytest.fixture
def sample_todo():
    return {"title": "Test todo", "description": "A test todo item"}


@pytest.fixture
def sample_user():
    return {"email": "test@example.com", "password": "secure123"}
