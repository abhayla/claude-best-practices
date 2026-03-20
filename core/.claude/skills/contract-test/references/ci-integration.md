# CI Integration

### CI Integration

```yaml
graphql-check:
  steps:
    - run: |
        graphql-inspector diff \
          "git:origin/main:schema.graphql" \
          "schema.graphql" \
          --rule suppressRemovalOfDeprecatedField
```

---

