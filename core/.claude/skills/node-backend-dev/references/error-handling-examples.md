# Error Handling Examples


### Custom AppError Class

```typescript
// src/middleware/error-handler.ts
export class AppError extends Error {
  constructor(
    public code: string,
    public statusCode: number,
    message: string,
    public details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

// Convenience factory functions
export const NotFound = (resource: string) =>
  new AppError('NOT_FOUND', 404, `${resource} not found`);
export const Unauthorized = (msg = 'Authentication required') =>
  new AppError('UNAUTHORIZED', 401, msg);
export const Forbidden = (msg = 'Insufficient permissions') =>
  new AppError('FORBIDDEN', 403, msg);
export const BadRequest = (msg: string, details?: Record<string, unknown>) =>
  new AppError('BAD_REQUEST', 400, msg, details);
export const Conflict = (msg: string) =>
  new AppError('CONFLICT', 409, msg);
```

### PostgreSQL Error Code Mapping

```typescript
function mapPgError(err: any): AppError {
  switch (err.code) {
    case '23505': // unique_violation
      return new AppError('CONFLICT', 409, 'Resource already exists', {
        constraint: err.constraint,
      });
    case '23503': // foreign_key_violation
      return new AppError('BAD_REQUEST', 400, 'Referenced resource not found');
    case '22P02': // invalid_text_representation
      return new AppError('BAD_REQUEST', 400, 'Invalid input syntax');
    case '23502': // not_null_violation
      return new AppError('BAD_REQUEST', 400, `Missing required field: ${err.column}`);
    default:
      return new AppError('INTERNAL_ERROR', 500, 'Database error');
  }
}
```

### Global Error Handler Per Framework

**Express:**

```typescript
import { Request, Response, NextFunction } from 'express';

export function errorHandler(err: Error, req: Request, res: Response, _next: NextFunction) {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: { code: err.code, message: err.message, ...(err.details && { details: err.details }) },
    });
  }

  // Map PostgreSQL errors
  if ((err as any).code && typeof (err as any).code === 'string' && (err as any).code.length === 5) {
    const mapped = mapPgError(err);
    return res.status(mapped.statusCode).json({
      error: { code: mapped.code, message: mapped.message, ...(mapped.details && { details: mapped.details }) },
    });
  }

  // Never expose stack traces in production
  console.error('Unhandled error:', err);
  res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' } });
}
```

**Hono:**

```typescript
import { HTTPException } from 'hono/http-exception';

app.onError((err, c) => {
  if (err instanceof AppError) {
    return c.json({
      error: { code: err.code, message: err.message, ...(err.details && { details: err.details }) },
    }, err.statusCode as any);
  }
  if (err instanceof HTTPException) {
    return c.json({ error: { code: 'HTTP_ERROR', message: err.message } }, err.status);
  }
  console.error('Unhandled error:', err);
  return c.json({ error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' } }, 500);
});
```

**ElysiaJS:**

```typescript
new Elysia()
  .error({ APP_ERROR: AppError })
  .onError(({ error, code, set }) => {
    if (error instanceof AppError) {
      set.status = error.statusCode;
      return {
        error: { code: error.code, message: error.message, ...(error.details && { details: error.details }) },
      };
    }
    console.error('Unhandled error:', error);
    set.status = 500;
    return { error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' } };
  });
```
