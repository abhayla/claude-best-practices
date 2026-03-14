# WebSocket Reference — Node.js Backend

Extended WebSocket examples for Express, Hono, and ElysiaJS.

## ElysiaJS (Bun Native WebSocket)

```typescript
import { Elysia, t } from 'elysia';

const app = new Elysia()
  .ws('/ws', {
    body: t.Object({
      type: t.String(),
      payload: t.Any(),
    }),
    open(ws) {
      console.log('Client connected');
    },
    message(ws, { type, payload }) {
      switch (type) {
        case 'join':
          ws.subscribe(`room:${payload.roomId}`);
          break;
        case 'message':
          ws.publish(`room:${payload.roomId}`, JSON.stringify({ type: 'message', payload }));
          break;
      }
    },
    close(ws) {
      console.log('Client disconnected');
    },
  });
```

## Express / Hono (ws Library on Node.js)

```typescript
import { WebSocketServer } from 'ws';
import type { Server } from 'http';

export function setupWebSocket(server: Server) {
  const wss = new WebSocketServer({ server });

  wss.on('connection', (ws, req) => {
    // Auth on connect — token in query param
    const url = new URL(req.url!, `http://${req.headers.host}`);
    const token = url.searchParams.get('token');
    if (!token) { ws.close(4001, 'Missing auth token'); return; }

    let user: any;
    try { user = verifyTokenSync(token); } catch { ws.close(4003, 'Invalid token'); return; }

    ws.on('message', (raw) => {
      const msg = JSON.parse(raw.toString()) as WsMessage;
      handleMessage(ws, user, msg);
    });

    ws.on('close', () => { /* cleanup subscriptions */ });
  });

  return wss;
}
```

## Hono WebSocket Helper (@hono/node-ws)

```typescript
import { Hono } from 'hono';
import { createNodeWebSocket } from '@hono/node-ws';

const app = new Hono();
const { injectWebSocket, upgradeWebSocket } = createNodeWebSocket({ app });

app.get('/ws', upgradeWebSocket((c) => ({
  onOpen(evt, ws) { console.log('Connected'); },
  onMessage(evt, ws) {
    const msg = JSON.parse(evt.data.toString());
    ws.send(JSON.stringify({ echo: msg }));
  },
  onClose() { console.log('Disconnected'); },
})));

const server = serve({ fetch: app.fetch, port: 3000 });
injectWebSocket(server);
```

## Typed Message Protocol (Discriminated Union)

```typescript
type WsMessage =
  | { type: 'join'; payload: { roomId: string } }
  | { type: 'leave'; payload: { roomId: string } }
  | { type: 'message'; payload: { roomId: string; content: string } }
  | { type: 'typing'; payload: { roomId: string; isTyping: boolean } };

function handleMessage(ws: WebSocket, user: AuthUser, msg: WsMessage) {
  switch (msg.type) {
    case 'join':    /* subscribe to room */ break;
    case 'leave':   /* unsubscribe from room */ break;
    case 'message': /* broadcast to room */ break;
    case 'typing':  /* broadcast typing indicator */ break;
    default:        ws.send(JSON.stringify({ type: 'error', payload: { message: 'Unknown type' } }));
  }
}
```

## Broadcaster Pattern

Hold a reference to the server so services can publish events without importing WebSocket code.

```typescript
class Broadcaster {
  private wss: WebSocketServer | null = null;

  attach(wss: WebSocketServer) { this.wss = wss; }

  publish(topic: string, data: unknown) {
    if (!this.wss) return;
    const message = JSON.stringify({ topic, data });
    this.wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(message);
      }
    });
  }

  publishToRoom(roomId: string, event: string, data: unknown) {
    this.publish(`room:${roomId}`, { event, ...data as object });
  }
}

export const broadcaster = new Broadcaster();
```
