import pytest
from sqlmodel import Session


# from .test_users import obj_1 as alice, obj_2 as bob, created_objs as created_users, path as user_path, objs as user_objs
# from .common import mkclient, session
import requests

            

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


def test_debug(session: Session):
    myobj = {
        'name': 'obj debug',
        'content': 'obj debug',
        'author': 1
    }
    client = mkclient()
    post_r = client.post('/posts', json=myobj)
    print(post_r.json())
    get_r = client.get('/posts')
    print(get_r.json())


if __name__ == '__main__':
    myobj = {
        'name': 'obj debug',
        'content': 'obj debug',
        'author': 1
    }
    endpoint = 'http://127.0.0.1:8000/posts'
    requests.post(endpoint, json=myobj)
    print(requests.get(endpoint).json())

    
