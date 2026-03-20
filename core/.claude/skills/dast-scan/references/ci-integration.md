# CI Integration

### CI Integration

```yaml
security-scan:
  runs-on: ubuntu-latest
  steps:
    - name: Conformance test
      run: specmatic test --contract openapi.yaml --host localhost --port 8000

    - name: OWASP ZAP API scan
      uses: zaproxy/action-api-scan@v0.7.0
      with:
        target: 'http://localhost:8000/openapi.json'
        format: openapi
        fail_action: true  # Fail CI on HIGH/CRITICAL findings

    - name: Upload security report
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: security-report
        path: report_html.html
```
