import pytest
from .common import mkclient
from .common import created_objs, session, objs, has_added_readonly_stuff, test_create, test_create_and_read_many


@pytest.fixture()
def path():
    return '/tagged_posts'

@pytest.fixture()
def obj_1():
    return {
        'tag_id': 1,
        'post_id': 1,
    }

@pytest.fixture()
def obj_2():
    return {
        'tag_id': 2,
        'post_id': 2
    }

@pytest.fixture()
def has_added_readonly_stuff():
    return lambda ignore1, ignore2: True


def test_create_and_read_one(path, obj_1):
    r = mkclient().get(f'{path}?post_id=1&tag_id=1')
    assert r.status_code == 200
    assert r.json() == [obj_1]


def test_delete_wrongly(created_objs, path, obj_1):
    client = mkclient()
    bad_id_delete = client.delete(f'{path}/1')
    assert bad_id_delete.status_code == 404
    bad_filter_delete = client.delete(f'{path}?post_id=1')
    assert bad_filter_delete.status_code == 422

def test_delete(created_objs, path):
    client = mkclient()
    read_all_request = client.get(path)
    assert len(read_all_request.json()) == 2
    delete_request = client.delete(f'{path}?post_id=1&tag_id=1')
    assert delete_request.status_code == 200
    assert delete_request.json() == {'ok': True}
    read_all_request_again = client.get(path)
    assert len(read_all_request_again.json()) == 1


