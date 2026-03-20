# Networking Best Practices

### Networking Best Practices

- Use custom bridge networks — never rely on the default bridge
- Service names are DNS hostnames within the same network
- Isolate frontend and backend into separate networks
- Only expose ports that external clients need

```yaml
networks:
  frontend:
  backend:
    internal: true  # No external access

services:
  proxy:
    networks: [frontend, backend]
  api:
    networks: [backend]
  db:
    networks: [backend]
```

---

