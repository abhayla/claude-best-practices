---
name: websocket-patterns
description: >
  WebSocket implementation patterns for real-time features across frameworks.
  Use when building real-time data streaming, live updates, chat, or push notifications.
allowed-tools: "Read Grep Glob"
argument-hint: "[server|client|reconnect|scaling]"
version: "1.0.0"
type: reference
triggers: websocket, ws, real-time, realtime, live-updates
---

# WebSocket Patterns Reference

Real-time WebSocket implementation across server frameworks and client platforms.

## Server Implementations

### FastAPI (Python)

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import dict

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, channel: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(channel, []).append(ws)

    def disconnect(self, channel: str, ws: WebSocket):
        self.active.get(channel, []).remove(ws)

    async def broadcast(self, channel: str, data: dict):
        for ws in self.active.get(channel, []):
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(channel, ws)

manager = ConnectionManager()

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await manager.connect(channel, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(channel, data)
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)
```

### Hono (TypeScript / Bun / Node)

```typescript
import { Hono } from "hono";
import { createBunWebSocket } from "hono/bun";

const { upgradeWebSocket, websocket } = createBunWebSocket();
const app = new Hono();

const channels = new Map<string, Set<WebSocket>>();

app.get("/ws/:channel", upgradeWebSocket((c) => {
  const channel = c.req.param("channel");
  return {
    onOpen(_event, ws) {
      if (!channels.has(channel)) channels.set(channel, new Set());
      channels.get(channel)!.add(ws.raw);
    },
    onMessage(event, ws) {
      const subscribers = channels.get(channel);
      if (!subscribers) return;
      for (const client of subscribers) {
        if (client !== ws.raw && client.readyState === WebSocket.OPEN) {
          client.send(typeof event.data === "string" ? event.data : JSON.stringify(event.data));
        }
      }
    },
    onClose(_event, ws) {
      channels.get(channel)?.delete(ws.raw);
    },
  };
}));

export default { fetch: app.fetch, websocket };
```

### ElysiaJS (Bun)

```typescript
import { Elysia } from "elysia";

const app = new Elysia()
  .ws("/ws/:channel", {
    open(ws) {
      ws.subscribe(ws.data.params.channel);
    },
    message(ws, message) {
      ws.publish(ws.data.params.channel, JSON.stringify(message));
    },
    close(ws) {
      ws.unsubscribe(ws.data.params.channel);
    },
  })
  .listen(3000);
```

### Express + ws

```typescript
import express from "express";
import { WebSocketServer, WebSocket } from "ws";
import http from "http";

const app = express();
const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: "/ws" });

wss.on("connection", (ws: WebSocket, req) => {
  ws.on("message", (data) => {
    // Broadcast to all other clients
    wss.clients.forEach((client) => {
      if (client !== ws && client.readyState === WebSocket.OPEN) {
        client.send(data);
      }
    });
  });

  ws.on("close", () => {
    // Cleanup
  });

  // Heartbeat
  ws.isAlive = true;
  ws.on("pong", () => { ws.isAlive = true; });
});

// Heartbeat interval to detect dead connections
setInterval(() => {
  wss.clients.forEach((ws) => {
    if (!ws.isAlive) return ws.terminate();
    ws.isAlive = false;
    ws.ping();
  });
}, 30000);

server.listen(3000);
```

## Client Implementations

### Browser / Vue / React

```typescript
class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private listeners = new Map<string, Set<(data: unknown) => void>>();

  constructor(url: string) {
    this.url = url;
    this.connect();
  }

  private connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log("WebSocket connected");
      this.reconnectDelay = 1000; // reset on success
    };

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      const handlers = this.listeners.get(msg.type);
      if (handlers) handlers.forEach((fn) => fn(msg.data));
    };

    this.ws.onclose = (event) => {
      if (!event.wasClean) this.reconnect();
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  private reconnect() {
    setTimeout(() => {
      this.connect();
      // Exponential backoff with jitter
      this.reconnectDelay = Math.min(
        this.reconnectDelay * 2 + Math.random() * 1000,
        this.maxReconnectDelay,
      );
    }, this.reconnectDelay);
  }

  on(type: string, handler: (data: unknown) => void) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set());
    this.listeners.get(type)!.add(handler);
    return () => this.listeners.get(type)?.delete(handler);
  }

  send(type: string, data: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }));
    }
  }

  close() {
    this.ws?.close();
  }
}
```

### Flutter / Dart

```dart
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';

class WsClient {
  WebSocketChannel? _channel;
  final String url;
  bool _shouldReconnect = true;

  WsClient(this.url);

  void connect() {
    _channel = WebSocketChannel.connect(Uri.parse(url));
    _channel!.stream.listen(
      (data) {
        final msg = jsonDecode(data as String);
        _handleMessage(msg);
      },
      onDone: () {
        if (_shouldReconnect) _reconnect();
      },
      onError: (_) {
        if (_shouldReconnect) _reconnect();
      },
    );
  }

  void send(Map<String, dynamic> data) {
    _channel?.sink.add(jsonEncode(data));
  }

  void _reconnect() {
    Future.delayed(const Duration(seconds: 2), connect);
  }

  void dispose() {
    _shouldReconnect = false;
    _channel?.sink.close();
  }

  void _handleMessage(Map<String, dynamic> msg) {
    // Override or use callbacks
  }
}
```

### Android / Kotlin (OkHttp)

```kotlin
import okhttp3.*

class WsClient(private val url: String) {
    private val client = OkHttpClient.Builder()
        .pingInterval(30, java.util.concurrent.TimeUnit.SECONDS)
        .build()
    private var ws: WebSocket? = null

    fun connect(listener: WebSocketListener) {
        val request = Request.Builder().url(url).build()
        ws = client.newWebSocket(request, listener)
    }

    fun send(message: String) {
        ws?.send(message)
    }

    fun close() {
        ws?.close(1000, "Client closing")
    }
}
```

## Message Protocol Design

### Typed Message Envelope

```typescript
interface WsMessage<T = unknown> {
  type: string;          // e.g., "market:tick", "order:update", "chat:message"
  data: T;
  timestamp: number;     // Unix ms
  id?: string;           // For deduplication / acknowledgment
}
```

### Common Message Types

| Type Pattern | Direction | Use |
|-------------|-----------|-----|
| `subscribe:channel` | Client → Server | Join a channel/topic |
| `unsubscribe:channel` | Client → Server | Leave a channel |
| `data:update` | Server → Client | Push new data |
| `ping` / `pong` | Bidirectional | Heartbeat |
| `error` | Server → Client | Error notification |
| `ack:messageId` | Server → Client | Delivery confirmation |

## Scaling Patterns

### Redis Pub/Sub for Multi-Server

```typescript
import Redis from "ioredis";

const pub = new Redis(process.env.REDIS_URL);
const sub = new Redis(process.env.REDIS_URL);

// On message from local client → publish to Redis
function broadcastToCluster(channel: string, data: unknown) {
  pub.publish(`ws:${channel}`, JSON.stringify(data));
}

// Subscribe to Redis → forward to local WebSocket clients
sub.psubscribe("ws:*");
sub.on("pmessage", (_pattern, channel, message) => {
  const wsChannel = channel.replace("ws:", "");
  // Send to all local clients subscribed to this channel
  localBroadcast(wsChannel, JSON.parse(message));
});
```

### Connection Lifecycle Best Practices

1. **Authentication**: Validate auth token in the upgrade request (query param or first message), not after connection
2. **Heartbeat**: Server pings every 30s, terminates connections that don't pong within 10s
3. **Reconnection**: Client uses exponential backoff with jitter (1s → 2s → 4s → ... → 30s cap)
4. **Graceful shutdown**: Server sends close frame, waits 5s, then terminates remaining connections
5. **Rate limiting**: Track messages per connection per second, disconnect abusers

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Connection drops after 60s | Proxy/LB idle timeout | Implement ping/pong heartbeat < 60s |
| Messages not reaching other clients | Single-server broadcast only | Use Redis pub/sub for multi-server |
| Client reconnects in tight loop | No backoff delay | Add exponential backoff with jitter |
| Memory growing on server | Dead connections not cleaned | Implement heartbeat + cleanup interval |
| `429` or connection refused | Too many connections | Rate limit connections per IP |
| Messages arriving out of order | Async broadcast | Add sequence numbers to messages |

## CRITICAL RULES

### MUST DO
- Always implement heartbeat/ping-pong (30s interval recommended)
- Always implement reconnection with exponential backoff and jitter on clients
- Always authenticate during the upgrade/handshake, not after connection
- Always handle connection cleanup on server (remove from maps/sets on close)
- Use Redis pub/sub when running multiple server instances behind a load balancer

### MUST NOT DO
- NEVER store sensitive data in WebSocket URLs (query params are logged) — use auth headers or first-message auth
- NEVER assume connections are permanent — always code for disconnection
- NEVER broadcast to all connections without channel filtering — it doesn't scale
- NEVER skip rate limiting on WebSocket messages — it's a DoS vector
