# 3.1 Project Structure

### 3.1 Project Structure

```
my-infra/
  Pulumi.yaml           # Project metadata
  Pulumi.dev.yaml       # Dev stack config
  Pulumi.staging.yaml   # Staging stack config
  Pulumi.prod.yaml      # Prod stack config
  __main__.py           # Python entry point (or index.ts for TypeScript)
  requirements.txt      # Python deps (or package.json for TypeScript)
```

```yaml
