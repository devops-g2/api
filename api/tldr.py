tldr_docs = """
Objects
-------

User:  (/users)
    id: int               (read-only)
    name: str
    username: str
    password: str

Category:  (/categories)
    id: int
    name: str

Thread:  (/threads)
    id: int               (read-only)
    name: str
    category_id: int
    author: int
    created_at: datetime  (read-only)
    updated_at: datetime  (read-only)

Post:  (/posts)
    id: int               (read-only)
    thread_id: int
    author: int
    content: str
    created_at: datetime  (read-only)
    updated_at: datetime  (read-only)


Endpoints: Special
------------------

GET /categories/<category_id>/threads
    Get a list of a category's thread IDs.

GET /threads/<thread_id>/posts
    Get a list of a thread's post IDs.


Endpoints: Generic CRUDs supported
----------------------------------

GET /<items> (?offset=0&limit=100)
    Get a list of items.

POST /<items>
    Create an item.

GET /<items>/<item_id>
    Get an item.

UPDATE /<items>/<item_id>
    Update an item.

DELETE /<items>
    Delete all items.

DELETE /<items>/<item_id>
    Delete an item.
""".lstrip()
