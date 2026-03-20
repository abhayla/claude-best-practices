# OWASP API Top 10 Mapping

### OWASP API Top 10 Mapping

Map tests to OWASP API Security Top 10 categories:

| OWASP Category | Test Approach | Automated |
|---------------|---------------|-----------|
| API1: Broken Object Level Auth | Request resource with different user's token | Yes |
| API2: Broken Authentication | Token expiry, brute force, credential stuffing | Yes |
| API3: Broken Object Property Level Auth | Modify read-only fields in PATCH/PUT | Yes |
| API4: Unrestricted Resource Consumption | Exceed rate limits, large payloads | Yes |
| API5: Broken Function Level Auth | Access admin endpoints with user token | Yes |
| API6: Unrestricted Access to Sensitive Business Flows | Automate business-critical flows | Partial |
| API7: Server Side Request Forgery | SSRF payloads in URL parameters | Yes |
| API8: Security Misconfiguration | Check headers, CORS, error disclosure | Yes |
| API9: Improper Inventory Management | Undocumented endpoints, old API versions | Yes |
| API10: Unsafe Consumption of APIs | Third-party API response validation | Partial |

