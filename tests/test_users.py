import pytest
from api.main import User
from api.models import *
from .common import session, add, mkclient


@pytest.fixture()
def users(session):
    alice = User.Creator(name='Alice', email='alice@example.com', password='123')
    bob = User.Creator(name='Bob', email='bob@example.com', password='456')
    for user in (alice, bob):
        add(session, user, User)


def test_users_exist(users):
    print('time to get')
    r = mkclient().get('/users')
    print(r)
    assert r.status_code == 200
