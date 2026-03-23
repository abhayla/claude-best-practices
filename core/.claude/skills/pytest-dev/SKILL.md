---
name: pytest-dev
description: >
  Apply pytest patterns for configuration, fixtures, parametrize, markers, async testing,
  mocking (monkeypatch, pytest-mock), plugins, and conftest.py. Use when writing
  or running Python tests with pytest.
allowed-tools: "Read Grep Glob"
triggers: "pytest, conftest, fixture, parametrize, monkeypatch, pytest-mock, python test"
argument-hint: "<pattern-to-look-up or 'config' or 'fixtures' or 'mock' or 'markers' or 'async'>"
version: "1.0.0"
type: reference
---

# Pytest Testing Reference

Pytest patterns for configuration, fixtures, parametrize, markers, async testing, mocking,
plugins, and conftest.py conventions. **Request:** $ARGUMENTS

---

## Configuration

### pyproject.toml (recommended)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers --tb=short"
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks integration tests",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:some_third_party.*",
]
```

### Key Command-Line Flags

| Flag | Purpose |
|------|---------|
| `-v` | Verbose output (show test names) |
| `-x` | Stop on first failure |
| `--lf` / `--ff` | Re-run last-failed only / failures first |
| `-k "expr"` | Run tests matching expression |
| `-m "marker"` | Run tests with specific marker |
| `--tb=short` / `--tb=no` | Shorter / no tracebacks |
| `-s` | Disable output capture (show prints) |
| `--co` | Collect-only (list tests without running) |
| `--strict-markers` | Error on unregistered markers |
| `--durations=10` | Show 10 slowest tests |

---

## Fixtures

### Scopes and Yield Teardown

```python
import pytest

@pytest.fixture
def sample_user():
    """Function-scoped (default) — fresh for each test."""
    return {"name": "Alice", "email": "alice@example.com"}

@pytest.fixture(scope="module")
def db_connection():
    """Module-scoped — shared across all tests in the module."""
    conn = create_connection()
    yield conn          # yield for teardown
    conn.close()

@pytest.fixture(scope="session")
def app_config():
    """Session-scoped — created once for entire test run."""
    return load_config(env="test")
```

Scope hierarchy: `function` (default) < `class` < `module` < `package` < `session`.

### Autouse Fixtures

```python
@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Applied to every test in scope without explicit request."""
    monkeypatch.setenv("APP_ENV", "test")
```

### Fixture Factories

```python
@pytest.fixture
def make_user():
    created = []
    def _make(name="Alice", role="user"):
        user = User(name=name, role=role)
        created.append(user)
        return user
    yield _make
    for user in created:
        user.delete()

def test_roles(make_user):
    admin = make_user(name="Bob", role="admin")
    regular = make_user(name="Carol", role="user")
    assert admin.can_access("/admin")
    assert not regular.can_access("/admin")
```

### tmp_path (built-in)

```python
def test_write_config(tmp_path):
    """tmp_path: unique temporary directory per test (pathlib.Path)."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"debug": true}')
    assert json.loads(config_file.read_text())["debug"] is True

@pytest.fixture(scope="session")
def shared_data_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("shared_data")
```

---

## Parametrize

```python
# Single parameter
@pytest.mark.parametrize("input_val,expected", [
    (1, "one"),
    (2, "two"),
    (3, "three"),
])
def test_number_to_word(input_val, expected):
    assert number_to_word(input_val) == expected

# Cartesian product — stacked decorators
@pytest.mark.parametrize("x", [1, 2])
@pytest.mark.parametrize("y", [10, 20])
def test_multiply(x, y):
    """Runs 4 tests: (1,10), (1,20), (2,10), (2,20)."""
    assert multiply(x, y) == x * y

# Custom IDs for readable output
@pytest.mark.parametrize("s,expected", [
    ("hello", 5), ("", 0), ("  spaces  ", 10),
], ids=["normal", "empty", "with-spaces"])
def test_string_length(s, expected):
    assert len(s) == expected
```

### Indirect Parametrize

```python
@pytest.fixture
def database_url(request):
    urls = {"sqlite": "sqlite:///test.db", "postgres": "postgresql://localhost/test"}
    return urls[request.param]

@pytest.mark.parametrize("database_url", ["sqlite", "postgres"], indirect=True)
def test_connection(database_url):
    assert connect(database_url).is_alive()
```

### Parametrize with Marks

```python
@pytest.mark.parametrize("n,expected", [
    (1, 1),
    (2, 4),
    pytest.param(3, 9, marks=pytest.mark.slow),
    pytest.param(-1, 1, marks=pytest.mark.xfail(reason="negative handling")),
])
def test_square(n, expected):
    assert square(n) == expected
```

---

## Markers

### Built-in Markers

```python
@pytest.mark.skip(reason="Feature not implemented yet")
def test_future_feature(): pass

@pytest.mark.skipif(sys.platform == "win32", reason="Unix-only test")
def test_unix_permissions(): pass

@pytest.mark.xfail(reason="Known bug", strict=True)
def test_known_bug():
    """strict=True: unexpected pass is a FAILURE."""
    assert broken_function() == "fixed"

@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_legacy_api():
    call_deprecated_api()
```

### Custom Markers and Selection

```python
# Register in pyproject.toml with --strict-markers:
# markers = ["slow: slow tests", "integration: integration tests"]

@pytest.mark.slow
def test_full_pipeline(): ...

@pytest.mark.integration
def test_external_api(): ...
```

```bash
pytest -m "not slow"              # Skip slow tests
pytest -m "integration"           # Only integration tests
pytest -m "not (slow or flaky)"   # Exclude multiple markers
```

---

## Async Testing

### pytest-asyncio Setup

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # auto-detect async tests (no decorator needed)
```

### Async Tests and Fixtures

```python
async def test_fetch_users():
    users = await fetch_users()
    assert len(users) > 0

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

async def test_get_endpoint(async_client):
    response = await async_client.get("/api/items")
    assert response.status_code == 200
```

---

## Mocking

### monkeypatch (built-in)

```python
def test_read_config(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    assert load_config().db_url == "sqlite:///test.db"

def test_override_method(monkeypatch):
    monkeypatch.setattr("<your-package>.services.payment.charge", lambda amount: True)
    assert process_order(amount=100).charged is True

def test_disable_network(monkeypatch):
    monkeypatch.delattr("socket.socket")  # Prevent accidental network calls

def test_override_dict(monkeypatch):
    config = {"retries": 5}
    monkeypatch.setitem(config, "retries", 1)
    assert config["retries"] == 1
```

### pytest-mock (mocker fixture)

```python
# pip install pytest-mock

def test_send_email(mocker):
    mock_send = mocker.patch("<your-package>.notifications.send_email")
    mock_send.return_value = {"status": "sent"}
    result = notify_user(user_id=1, message="Hello")
    mock_send.assert_called_once_with(to="user@example.com", subject=mocker.ANY, body="Hello")

def test_database_error(mocker):
    mocker.patch("<your-package>.db.repository.save", side_effect=ConnectionError("DB unreachable"))
    with pytest.raises(ServiceError, match="Failed to save"):
        create_record(data={"key": "value"})

def test_spy_on_method(mocker):
    spy = mocker.spy(MyService, "process")
    MyService().run()
    spy.assert_called_once()

def test_mock_property(mocker):
    mocker.patch.object(MyService, "is_ready", new_callable=mocker.PropertyMock, return_value=True)
    assert MyService().is_ready is True
```

### Patching Strategy

```python
# Patch WHERE IT IS USED, not where it is defined.
# If <your-package>.views imports send_email from <your-package>.notifications:
mocker.patch("<your-package>.views.send_email")          # CORRECT
mocker.patch("<your-package>.notifications.send_email")   # WRONG — views already imported it
```

---

## Plugins

| Plugin | Install | Purpose |
|--------|---------|---------|
| pytest-cov | `pip install pytest-cov` | Coverage reporting |
| pytest-xdist | `pip install pytest-xdist` | Parallel test execution |
| pytest-timeout | `pip install pytest-timeout` | Per-test timeouts |
| pytest-repeat | `pip install pytest-repeat` | Run tests N times (flaky detection) |
| pytest-randomly | `pip install pytest-randomly` | Randomize test order |
| pytest-sugar | `pip install pytest-sugar` | Better progress bar output |

### Coverage Configuration

```toml
# pyproject.toml
[tool.coverage.run]
source = ["<your-package>"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
show_missing = true
fail_under = 80
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:"]
```

```bash
pytest --cov=<your-package> --cov-report=term-missing --cov-fail-under=80
```

### Parallel Execution

```bash
pytest -n auto                  # All CPU cores
pytest -n 4                     # 4 workers
pytest -n auto --dist=loadfile  # Group by file (preserves module fixtures)
```

### Flaky Detection and Timeouts

```bash
pytest --count=5 -x             # Run each test 5 times, stop on first failure
pytest --timeout=10             # 10-second timeout per test
pytest --randomly-seed=12345    # Reproduce specific random ordering
```

---

## conftest.py Patterns

### Layered conftest.py Files

```
tests/
  conftest.py              # Shared: db, client, factories
  unit/
    conftest.py            # Unit: mocked services, in-memory stores
    test_models.py
  integration/
    conftest.py            # Integration: real db connections
    test_api.py
```

### Test Client and Auth Fixture

```python
@pytest.fixture(scope="session")
def app():
    return create_app(config="testing")

@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client

@pytest.fixture
def auth_client(client, make_user):
    user = make_user(role="admin")
    client.environ_base["HTTP_AUTHORIZATION"] = f"Bearer {generate_token(user)}"
    return client
```

---

## Commands

```bash
pytest                                          # Run all tests
pytest tests/test_users.py                      # Single file
pytest tests/test_users.py::test_create         # Single test
pytest tests/test_users.py::TestClass::test_m   # Class method
pytest -k "create and not delete"               # Match expression
pytest -m slow                                  # By marker
pytest --lf                                     # Last-failed only
pytest -x --pdb                                 # Debug on failure
pytest --co -q                                  # List tests without running
pytest --fixtures                               # List available fixtures
pytest -n auto --cov=<your-package>                      # Parallel + coverage
```

---

## CRITICAL RULES

- Always patch where the name is USED, not where it is DEFINED -- `mocker.patch("<your-package>.views.send_email")` not `mocker.patch("<your-package>.notifications.send_email")` when views imports send_email
- Use `yield` fixtures for cleanup instead of `try/finally` -- pytest guarantees teardown runs even on test failure
- Register custom markers in `pyproject.toml` and use `--strict-markers` -- unregistered markers silently become no-ops
- Use `tmp_path` (pathlib.Path) instead of the deprecated `tmpdir` (py.path.local) -- `tmp_path` is the modern API
- Use `autouse=True` sparingly -- it runs for EVERY test in scope, wasting time and hiding dependencies; prefer explicit fixture injection
- Never share mutable state between tests -- use function-scoped fixtures; session-scoped fixtures must be read-only or use isolation (e.g., transaction rollback)
- Prefer `pytest.raises(ExceptionType, match="pattern")` over bare `try/except` -- validates both type and message
- Use `-x --lf` during development for fast feedback -- stop on first failure, re-run only last-failed
- Set `asyncio_mode = "auto"` in pyproject.toml when using pytest-asyncio -- avoids forgetting `@pytest.mark.asyncio` decorators
- Use `--dist=loadfile` with pytest-xdist when tests share module-scoped fixtures -- default distribution causes redundant fixture creation
- Scope expensive resources to `session` only (db connections, app instances) -- broader scopes increase test pollution risk
