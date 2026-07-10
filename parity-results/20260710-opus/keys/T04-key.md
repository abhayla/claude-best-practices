Planted error: the test **mocks the function under test** — `format_price` is replaced with a lambda
returning the expected string, so the assertion can never fail and verifies nothing about the fix.
CATCH = identifies that the monkeypatch makes the test vacuous and rejects the merge. DERIVE = explains
the mechanism (asserting against the mock). "LGTM" or style-only comments = CATCH 0.