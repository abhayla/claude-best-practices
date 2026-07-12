# CI Integration

### CI Integration

```yaml
proto-check:
  steps:
    - uses: bufbuild/buf-setup-action@v1
    - run: buf lint
    - run: buf breaking --against 'https://github.com/$REPO.git#branch=main'
```

---

