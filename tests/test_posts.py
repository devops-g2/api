import pytest


@pytest.fixture()
def path():
    # for user in user_objs:
    return "/posts"


@pytest.fixture()
def obj_1():
    return {"name": "obj 1", "content": "obj 1", "author": 1}


@pytest.fixture()
def has_added_readonly_stuff():
    def has_added_readonly_stuff(data, obj, **kwargs):
        keys = {"name", "content", "author", "id", "updated_at", "created_at", "tags"}
        return set(data.keys()) == keys

    return has_added_readonly_stuff


@pytest.fixture()
def obj_2():
    return {"name": "obj 2", "content": "obj 2", "author": 1}


@pytest.fixture()
def patched_obj_1():
    return {"author": 1}
