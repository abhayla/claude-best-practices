# Firebase App Hosting (SSR Frameworks)

### When to Use Which

| Use Case | Service |
|----------|---------|
| Static HTML/CSS/JS, SPA (React/Vue without SSR) | Firebase Hosting |
| Next.js / Angular with SSR or ISR | App Hosting |
| Automated git-push-to-deploy | App Hosting |

### Configuration (apphosting.yaml)

```yaml
runConfig:
  minInstances: 0
  maxInstances: 4
  cpu: 1
  memoryMiB: 512
  concurrency: 80

env:
  - variable: NEXT_PUBLIC_API_URL
    value: "https://api.example.com"
  - variable: API_KEY
    secret: my-api-key    # References Cloud Secret Manager
```

### firebase.json

```json
{
  "apphosting": {
    "backendId": "my-app-id",
    "rootDir": "/",
    "ignore": ["node_modules", ".git", "functions"]
  }
}
```

### CLI Commands

```bash
