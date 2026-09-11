import os

import pytest
from fastapi import HTTPException

from security import Principal, require_role


def test_require_role_accepts_allowed_role():
    principal = Principal(user_id="u-1", role="admin")
    assert require_role(principal, "admin").user_id == "u-1"


def test_require_role_rejects_disallowed_role():
    principal = Principal(user_id="u-1", role="taxpayer")
    with pytest.raises(HTTPException) as exc:
        require_role(principal, "admin")
    assert exc.value.status_code == 403
