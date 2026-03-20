# Logging Configuration

### Logging Configuration

```yaml
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"   # Rotate at 10MB
        max-file: "3"     # Keep 3 rotated files
        compress: "true"
```

---

