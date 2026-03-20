# STEP 2: Server Functionality

### API Routes (defineEventHandler)

```typescript
// server/api/users.get.ts — GET /api/users
export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  // Return data directly — auto-serialized to JSON
  return { users: [] }
})

// server/api/users.post.ts — POST /api/users
export default defineEventHandler(async (event) => {
  const body = await readBody(event)
  // Validate and create user
  return { id: 1, ...body }
})

// server/api/users/[id].get.ts — GET /api/users/:id
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  return { id }
})
```

### Input Validation

```typescript
// server/api/users.post.ts
export default defineEventHandler(async (event) => {
  const body = await readValidatedBody(event, (data) => {
    // Use Zod or manual validation
    if (!data?.email) throw createError({ statusCode: 400, message: 'Email required' })
    return data as { email: string; name: string }
  })
  return body
})
```

### Error Handling

```typescript
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')
  const item = await findItem(id)
  if (!item) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Item not found',
    })
  }
  return item
})
```

### WebSocket Handler

```typescript
// server/routes/_ws.ts
export default defineWebSocketHandler({
  open(peer) {
    peer.send(JSON.stringify({ message: 'Connected' }))
    peer.subscribe('chat')
  },
  message(peer, message) {
    peer.publish('chat', message.text())
  },
  close(peer) {
    peer.unsubscribe('chat')
  },
})
```

### Server-Sent Events (SSE)

```typescript
// server/api/stream.get.ts
export default defineEventHandler(async (event) => {
  const stream = createEventStream(event)
  let count = 0
  const interval = setInterval(async () => {
    await stream.push({ data: JSON.stringify({ count: ++count }) })
  }, 1000)
  stream.onClosed(() => clearInterval(interval))
  return stream.send()
})
```

---

