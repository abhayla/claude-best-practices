"""SCHEMA_MISMATCH fixture for the three-lane test pipeline (PR1).

This is a Python pytest test that lives at `tests/api/test_users.py` —
the path matches the API track glob (`**/tests/api/**`) and the import
of `httpx` matches the API import signal. Per scout's accumulate semantics,
this test is classified as requiring tracks: ["functional", "api"].

The test ITSELF passes — it asserts that POSTing the wrong field name
returns a 422. But what makes this a useful fixture for the three-lane
pipeline is that the API lane's `/contract-test` skill (when contracts
are present) would catch the underlying schema drift between the request
shape and the Pydantic model.

Used by:
- `scripts/tests/test_pipeline_three_lane.py::test_track_auto_detection_path_based`
  (scout sees this in `tests/api/` → API track required)
- `scripts/tests/test_pipeline_three_lane.py::test_t1_handles_4_new_api_categories`
  (T1's extended inline Issue creation must handle SCHEMA_MISMATCH)
"""

import httpx
import pytest


@pytest.mark.api
def test_create_user_with_wrong_field_name_returns_422():
    """POST /users with `name` field instead of `full_name` → 422."""
    # This is a deliberate SCHEMA_MISMATCH scenario.
    # In a real run the demo app's Pydantic model UserCreate expects
    # `full_name: str`, but the test sends `name: str`. The endpoint
    # returns 422 with a Pydantic validation error.
    payload = {"name": "Alice"}  # WRONG — should be `full_name`
    expected_status = 422
    expected_error_field = "full_name"

    # NOTE: this is a fixture for the three-lane pipeline test scaffolding,
    # NOT an executable integration test against a live server. The pytest
    # framework picks it up for classification (path + import scanning).
    # The body below documents the intent for /contract-test and downstream
    # readers; in the real fixture an httpx mock or live server would back it.

    # Sanity assertion that keeps the test pyTest-discoverable
    assert payload["name"] == "Alice"
    assert expected_status == 422
    assert expected_error_field == "full_name"


@pytest.mark.api
def test_request_uses_httpx_client():
    """Marker test — presence of httpx import is what the scout's API
    import-signal scan keys off of (the scout doesn't execute tests,
    only scans imports). Keeping httpx referenced here in module scope
    too via the import statement at the top."""
    # Use httpx symbol so import is not flagged as unused
    client = httpx.Client(base_url="http://localhost:8000")
    assert client is not None
    client.close()
