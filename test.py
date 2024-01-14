import requests

obj = {
    "name": "Glöm inte registrera er närvaro",
    "content": "Verkligen! Glöm inte det!",
    "author": 1,
}

# tag_id

#     'tag

r = requests.post("http://127.0.0.1:8000/posts", json=obj)
print(r.status_code)
print(r.text)
r2 = requests.get("http://127.0.0.1:8000/posts")
print(r2.status_code)
print(r2.text)
