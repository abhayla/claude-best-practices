# STEP 5: Improve Readability

### 5a. Standardize naming conventions

Check test naming against the project's dominant convention:

| Convention | Example |
|-----------|---------|
| `test_<action>_<condition>_<expected>` | `test_login_with_invalid_password_returns_401` |
| `should <behavior> when <condition>` | `should return 401 when password is invalid` |
| `<method>_<scenario>_<result>` | `login_invalidPassword_returns401` |

Flag tests that deviate from the dominant pattern. Suggest renames but do NOT
auto-rename without user approval.

### 5b. Enforce Arrange-Act-Assert (AAA) pattern

Scan test bodies for structure:
- **Arrange**: Setup/fixture code at the top
- **Act**: Single action being tested (one function call or request)
- **Assert**: Verification at the bottom

Flag tests that:
- Mix assertions throughout the body (interleaved act-assert)
- Have no clear separation between phases
- Contain multiple unrelated actions

### 5c. Consolidate inline test data

Find tests with hardcoded test data that should be extracted:
- Magic numbers repeated across tests
- Inline JSON/dict/object literals duplicated in multiple tests
- String constants used in assertions that could be factory-generated

Recommend extracting to:
- **Python:** `conftest.py` fixtures or a `factories.py` using `factory_boy` or similar
- **JavaScript:** Shared test helpers or a `factories/` directory

---

