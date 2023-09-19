import pytest
from sqlmodel import Session


# from .test_users import obj_1 as alice, obj_2 as bob, created_objs as created_users, path as user_path, objs as user_objs
from .common import *
# import requests

            

@pytest.fixture()
def path():
    # for user in user_objs:
    #     mkclient().post(user_path, json=user)
    return '/posts'

@pytest.fixture()
def obj_1():
    obj_1 = {
        'name': 'obj 1',
        'content': 'obj 1',
        'author': 1
    }
    return obj_1

@pytest.fixture()
def has_added_readonly_stuff():
    def has_added_readonly_stuff(data, obj, **kwargs):
        keys = {
            'name', 'content', 'author', 'id', 'updated_at', 'created_at', 'tags'
        }
        return set(data.keys()) == keys
    return has_added_readonly_stuff

@pytest.fixture()
def obj_2():
    obj_2 = {
        'name': 'obj 2',
        'content': "obj 2",
        'author': 1
    }
    return obj_2

