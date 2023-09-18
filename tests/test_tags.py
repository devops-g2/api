import pytest
from sqlmodel import Session

from api.models import User

from .common import *
import requests

@pytest.fixture()
def path():
    return '/tags'

@pytest.fixture()
def obj_1():
    obj_1 = {
        'name': 'Art',
    }
    return obj_1

@pytest.fixture()
def obj_2():
    obj_2 = {
        'name': 'Big Data',
    }
    return obj_2

@pytest.fixture()
def objs(obj_1, obj_2):
    return obj_1, obj_2
