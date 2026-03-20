# ZAP Rules File (zap-rules.tsv)

### ZAP Rules File (zap-rules.tsv)

```tsv
10010	IGNORE	# Cookie without Secure flag (dev only)
10011	IGNORE	# Cookie without HttpOnly flag (dev only)
10015	FAIL	# Incomplete or no CSP
10021	FAIL	# X-Content-Type-Options missing
10038	FAIL	# Content-Security-Policy missing
40012	FAIL	# XSS Reflected
40014	FAIL	# XSS Persistent
40018	FAIL	# SQL Injection
90033	FAIL	# Loosely Scoped Cookie
```

---

