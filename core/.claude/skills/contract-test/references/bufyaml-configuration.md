# buf.yaml Configuration

### buf.yaml Configuration

```yaml
version: v2
lint:
  use:
    - DEFAULT          # Standard lint rules
    - COMMENTS         # Require comments on services/messages
  except:
    - PACKAGE_VERSION_SUFFIX  # Allow unversioned packages
breaking:
  use:
    - FILE             # Detect breaking changes per file
```

