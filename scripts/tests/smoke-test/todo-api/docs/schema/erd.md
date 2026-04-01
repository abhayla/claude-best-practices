# Entity Relationship Diagram

## Tables

### users
| Column | Type | Constraints |
|--------|------|------------|
| id | UUID | PK |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| created_at | TIMESTAMP | NOT NULL DEFAULT now() |

### todos
| Column | Type | Constraints |
|--------|------|------------|
| id | UUID | PK |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | NULLABLE |
| completed | BOOLEAN | NOT NULL DEFAULT false |
| user_id | UUID | FK -> users.id |
| created_at | TIMESTAMP | NOT NULL DEFAULT now() |

## Relationships
- users 1:N todos (one user has many todos)
