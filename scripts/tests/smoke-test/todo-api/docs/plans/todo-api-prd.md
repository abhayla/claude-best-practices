# PRD: Todo API

## Meta
- Author: Claude Code
- Date: 2026-01-15
- Status: APPROVED
- Version: 1.0

## Scope
A RESTful API for managing todo items with user authentication.

## Overview
Build a FastAPI-based todo list API supporting CRUD operations, user auth, and task prioritization.

## User Stories
- US-001: As a user, I want to create a todo item so that I can track tasks
- US-002: As a user, I want to list my todos so that I can see pending work
- US-003: As a user, I want to update a todo so that I can mark it complete
- US-004: As a user, I want to delete a todo so that I can remove finished tasks
- US-005: As a user, I want to register an account so that my todos are private
- US-006: As a user, I want to login so that I can access my todos

## Acceptance Criteria
- AC-001 (US-001): Given a valid title, when POST /todos, then return 201 with todo object
- AC-002 (US-002): Given an authenticated user, when GET /todos, then return list of user's todos
- AC-003 (US-003): Given a valid todo ID, when PATCH /todos/{id}, then update and return todo
- AC-004 (US-004): Given a valid todo ID, when DELETE /todos/{id}, then return 204
- AC-005 (US-005): Given valid credentials, when POST /auth/register, then create user account
- AC-006 (US-006): Given valid credentials, when POST /auth/login, then return JWT token

## Non-Functional Requirements

| ID | Characteristic | Requirement | Target |
|----|---------------|-------------|--------|
| NFR-001 | Performance Efficiency | Response time for CRUD operations | p95 < 200ms |
| NFR-002 | Security | JWT authentication required for all todo endpoints | Bearer token |
| NFR-003 | Reliability | Service availability | 99.5% uptime |
| NFR-004 | Maintainability | Test coverage | >= 80% |

## Risk Register
| ID | Risk | Probability (1-5) | Impact (1-5) | Score | Mitigation |
|----|------|:-:|:-:|:-:|-----------|
| RISK-001 | JWT token leakage | 2 | 4 | 8 | Use short-lived tokens with refresh |

## Requirement Tiers (MoSCoW)
### Must Have (MVP)
- REQ-M001: CRUD operations for todos [US-001, AC-001]
- REQ-M002: User authentication [US-005, AC-005]
- REQ-M003: Authorization per user [US-006, AC-006]

### Should Have (v1.1)
- REQ-S001: Todo prioritization [US-001]

### Won't Have (out of scope)
- REQ-W001: Real-time collaboration — not needed for MVP
