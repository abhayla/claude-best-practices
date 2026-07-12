# Pipeline Flow

### Pipeline Flow

```
Consumer CI:  test → publish pact → can-i-deploy → deploy
Provider CI:  test → verify pacts → publish results → can-i-deploy → deploy
```

Both consumer and provider MUST pass `can-i-deploy` before deploying to any shared environment.

---

