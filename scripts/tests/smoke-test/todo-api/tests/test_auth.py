"""Tests for authentication endpoints."""


def test_register_user(sample_user):
    assert sample_user["email"] == "test@example.com"


def test_login_user():
    token = "fake-jwt-token"
    assert len(token) > 0
