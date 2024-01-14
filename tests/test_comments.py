import pytest

from .common import *


@pytest.fixture()
def path():
    return "/comments"


@pytest.fixture()
def obj_1():
    return {
        "content": "Foo\nbar\nbaz",
        "author": 0,
        "post_id": 0
    }


@pytest.fixture()
def obj_2():
    return {
        "content": "AAA\nBBB",
        "author": 1,
        "post_id": 1
    }



@pytest.fixture()
def patched_obj_1():
    return {"content": "Quox"}

@pytest.fixture()
def has_added_readonly_stuff():
    def has_added_readonly_stuff(data, obj, **kwargs):
        keys = {"id", "content", "author", "post_id", "author", "created_at", "updated_at"}
        return set(data.keys()) == keys

    return has_added_readonly_stuff
 
