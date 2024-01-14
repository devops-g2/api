import pytest

from .common import *


@pytest.fixture()
def path():
    return "/tags"


@pytest.fixture()
def obj_1():
    return {
        "name": "Art",
    }


@pytest.fixture()
def obj_2():
    return {
        "name": "Big Data",
    }


@pytest.fixture()
def patched_obj_1():
    return {"name": "Tra"}
