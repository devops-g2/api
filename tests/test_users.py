import pytest

from .common import *


@pytest.fixture()
def path():
    return "/users"


@pytest.fixture()
def obj_1():
    return {
        "name": "Alice",
        "email": "alice@example.com",
        "password": "alice_password",
    }


@pytest.fixture()
def obj_2():
    return {"name": "Bob", "email": "bob@example.com", "password": "bob_password"}


@pytest.fixture()
def patched_obj_1():
    return {"name": "Not Alice"}
