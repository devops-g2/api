import pytest
from sqlmodel import Session

from api.models import User

from .common import *
import requests

@pytest.fixture()
def path():
    return '/users'

@pytest.fixture()
def obj_1():
    obj_1 = {
        'name': 'Alice',
        'email': 'alice@example.com',
        'password': 'alice_password'
    }
    return obj_1

@pytest.fixture()
def obj_2():
    obj_2 = {
        'name': 'Bob',
        'email': 'bob@example.com',
        'password': 'bob_password'
    }
    return obj_2

