---
name: pm2-deploy
description: >
  Configure PM2 process management and deployment for Node.js and Python
  applications. Use when setting up PM2 ecosystem files, managing processes,
  or deploying to production. NOT for deployment strategies (use /deploy-strategy)
  or FastAPI-specific orchestration (use /fastapi-deploy).
allowed-tools: "Read Grep Glob"
argument-hint: "[setup|status|deploy|logs]"
version: "1.1.0"
type: reference
triggers:
  - pm2
  - pm2 deploy
  - pm2 ecosystem config
  - process manager node
  - pm2 cluster mode
  - pm2 setup production
---

# PM2 Deployment Reference

PM2 process management for Node.js, Next.js, and static site deployments.

## Ecosystem Configuration

### Basic ecosystem.config.js

```javascript
module.exports = {
  apps: [
    {
      name: "web",
      script: "node_modules/.bin/next",
      args: "start",
      cwd: "/path/to/project",
      instances: "max",        // cluster mode, one per CPU
      exec_mode: "cluster",
      env: {
        NODE_ENV: "production",
        PORT: 3000,
      },
      // Restart policies
      max_memory_restart: "500M",
      restart_delay: 5000,
      max_restarts: 10,
      min_uptime: "10s",
      // Logging
      error_file: "./logs/error.log",
      out_file: "./logs/out.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
    },
  ],
};
```

### Multi-App Configuration

```javascript
module.exports = {
  apps: [
    {
      name: "web",
      script: "node_modules/.bin/next",
      args: "start",
      cwd: "/path/to/project/apps/web",
      instances: "max",
      exec_mode: "cluster",
      env: { NODE_ENV: "production", PORT: 3000 },
    },
    {
      name: "api",
      script: "dist/server.js",
      cwd: "/path/to/project/apps/api",
      instances: 2,
      exec_mode: "cluster",
      env: { NODE_ENV: "production", PORT: 4000 },
    },
    {
      name: "scraper",
      script: "dist/scraper.js",
      cwd: "/path/to/project/apps/scraper",
      instances: 1,
      exec_mode: "fork",       // single instance for cron-like tasks
      cron_restart: "0 */6 * * *",  // restart every 6 hours
      autorestart: false,
      env: { NODE_ENV: "production" },
    },
    {
      name: "static",
      script: "node_modules/.bin/serve",
      args: "-s out -l 3002",   // serve static export
      cwd: "/path/to/project",
      instances: 1,
      exec_mode: "fork",
      env: { NODE_ENV: "production" },
    },
  ],
};
```

### Python/FastAPI with PM2

```javascript
module.exports = {
  apps: [
    {
      name: "api",
      script: "uvicorn",
      args: "app.main:app --host 0.0.0.0 --port 8000 --workers 4",
      cwd: "/path/to/project/backend",
      interpreter: "python3",
      env: { PYTHONPATH: "." },
    },
  ],
};
```

## Essential Commands

### Process Management

```bash
# Start all apps from ecosystem file
pm2 start ecosystem.config.js

# Start specific app
pm2 start ecosystem.config.js --only web

# Restart / reload (zero-downtime for cluster mode)
pm2 reload web            # zero-downtime reload (cluster only)
pm2 restart web           # hard restart

# Stop / delete
pm2 stop web
pm2 delete web
pm2 delete all

# List processes
pm2 list
pm2 jlist                 # JSON output

# Monitor (live dashboard)
pm2 monit
```

### Startup and Persistence

```bash
# Generate startup script (survives server reboot)
pm2 startup               # outputs a command to run with sudo

# Save current process list
pm2 save

# Resurrect saved processes
pm2 resurrect
```

### Logs

```bash
# Stream all logs
pm2 logs

# Stream specific app
pm2 logs web --lines 100

# Flush logs
pm2 flush

# Install log rotation
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 50M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
```

## Deployment Workflow

### Zero-Downtime Deploy Script

```bash
#!/bin/bash
set -euo pipefail

APP_DIR="/path/to/project"
cd "$APP_DIR"

echo "Pulling latest changes..."
git pull origin main

echo "Installing dependencies..."
npm ci --production

echo "Building..."
npm run build

echo "Reloading PM2 processes..."
pm2 reload ecosystem.config.js

echo "Saving PM2 state..."
pm2 save

echo "Deploy complete."
```

### Health Check After Deploy

```bash
# Check all processes are online
pm2 jlist | jq '.[].pm2_env.status' | grep -v '"online"' && echo "UNHEALTHY" || echo "ALL HEALTHY"

# Check specific app responds
curl -sf http://localhost:3000/api/health || (echo "Health check failed" && pm2 logs web --lines 50)
```

## Cluster Mode vs Fork Mode

| Feature | Cluster | Fork |
|---------|---------|------|
| Multiple instances | Yes (`instances: "max"`) | No (single process) |
| Zero-downtime reload | Yes (`pm2 reload`) | No (uses restart) |
| Use for | Web servers, APIs | Workers, cron jobs, scripts |
| `exec_mode` | `"cluster"` | `"fork"` |
| Load balancing | Built-in round-robin | N/A |

## Environment Management

```javascript
module.exports = {
  apps: [{
    name: "web",
    script: "dist/server.js",
    // Default env
    env: {
      NODE_ENV: "production",
      PORT: 3000,
    },
    // Override with: pm2 start ecosystem.config.js --env staging
    env_staging: {
      NODE_ENV: "staging",
      PORT: 3001,
    },
  }],
};
```

## Nginx Integration

```nginx
upstream app_servers {
    server 127.0.0.1:3000;
    # Add more if running multiple ports
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://app_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Troubleshooting

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| App keeps restarting | `pm2 logs app --lines 50` | Fix crash cause; check `min_uptime` and `max_restarts` |
| Port already in use | `pm2 list` shows stale process | `pm2 delete all` then restart |
| Processes lost after reboot | Startup script not configured | Run `pm2 startup` then `pm2 save` |
| High memory usage | Memory leak in app | Set `max_memory_restart` |
| Cluster reload not zero-downtime | App takes too long to start | Add `listen_timeout` or `kill_timeout` |
| Logs filling disk | No rotation configured | Install `pm2-logrotate` |

## CRITICAL RULES

### MUST DO
- Always use `pm2 reload` (not `restart`) for zero-downtime deploys in cluster mode
- Always run `pm2 save` after changing process list
- Always configure `pm2 startup` on production servers
- Always set `max_memory_restart` to prevent memory leak crashes
- Always configure log rotation (`pm2-logrotate`) in production
- Use `npm ci --production` (not `npm install`) in deploy scripts

### MUST NOT DO
- NEVER use `pm2 restart` for zero-downtime requirements — use `reload` with cluster mode
- NEVER store secrets in `ecosystem.config.js` — use environment variables or `.env` files
- NEVER commit `ecosystem.config.js` with absolute paths to production servers — use environment variables
- NEVER use `pm2 start app.js` in production without an ecosystem file — it's not reproducible
