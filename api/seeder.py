import httpx
import asyncio
from abc import ABC, abstractmethod
from inflection import tableize

BASE_URL = r'http://127.0.0.1:8000'


class Seeder(ABC):

    @classmethod
    @abstractmethod
    def objs(cls):
        ...

    @classmethod
    def wait_for(cls):
        return []

    @classmethod
    def path(cls):
        return '/' + tableize(cls.__name__.removesuffix('Seeder'))

    @classmethod
    async def seed(cls):
        if cls.wait_for():
            await asyncio.gather(*(
                waited_cls.seed_done.wait()
                for waited_cls in cls.wait_for()
            ))

        await asyncio.gather(*[
            asyncio.create_task(cls.client.post(BASE_URL + cls.path(), json=obj))
            for obj in cls.objs()
        ])

        cls.seed_done.set()
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.seed_done = asyncio.Event()

    @classmethod
    def seed_all(cls):
        return asyncio.gather(*(
            subclass.seed()
            for subclass in cls.__subclasses__()
        ))

    @classmethod
    def init_client(cls, client):
        cls.client = client


class UserSeeder(Seeder):
    # @classmethod
    # def path(cls):
    #     return '/users'
    
    @classmethod
    def objs(cls):
        return [
            {
                'name': 'Alice',
                'email': 'alice@example.com',
                'password': 'alice_password'
            },
            {
                'name': 'Bob',
                'email': 'bob@example.com',
                'password': 'bob_password'
            },
            {
                'name': 'Charlie',
                'email': 'charlie@example.com',
                'password': 'charlie_password'
            },
        ]


class TagSeeder(Seeder):
    # @classmethod
    # def path(cls):
    #     return '/tags'

    @classmethod
    def objs(cls):
        return [
            {
                'name': 'Tag',
            },
            {
                'name': 'Arts & Crafts',
            },
            {
                'name': 'Tag2',
            },
        ]


class PostSeeder(Seeder):
    @classmethod
    def wait_for(cls):
        return [
            UserSeeder
        ]

    # @classmethod
    # def path(cls):
    #     return '/posts'

    @classmethod
    def objs(cls):
        return [
            {
                'name': 'Whispers in the Wind',
                'author': 1,
                'content': '''
                    Beneath the ancient trees, a secret game,
                    Tag, where whispers in the wind proclaim.
                    Through dappled sunlight and mossy embrace,
                    Chasing echoes, in a timeless space.

                    Laughter lingers, like leaves in the air,
                    Tag, a dance with nature, beyond compare.
                    In the forest's heart, a childhood's song,
                    Where innocence and joy belong.
                ''',
            },
            {
                'name': 'Canvas of Dreams',
                'author': 2,
                'content': '''
                    Arts & Crafts, an enchanting affair,
                    Brushstrokes of passion in the evening air.
                    From paper to canvas, a journey starts,
                    Crafting dreams with creative hearts.

                    Colors blend like a cosmic ballet,
                    Imagination, the artist's gateway.
                    In every stroke, a story unfolds,
                    A masterpiece in hues and molds.
                '''
            },
            {
                'name': 'Cyber Symphony',
                'author': 3,
                'content': '''
                    Tag2, a digital melody,
                    In the vast expanse of technology.
                    Bytes and bits, a cybernetic sea,
                    Tag2, where connections can be free.

                    In the realm of codes and binary,
                    Tag2, a dance of virtual symphony.
                    Through pixels and data, identities align,
                    In the digital tapestry, where echoes intertwine.
                '''
            }
        ]


class TaggedPostSeeder(Seeder):
    @classmethod
    def wait_for(cls):
        return [
            PostSeeder,
            TagSeeder
        ]

    # @classmethod
    # def path(cls):
    #     return '/tagged_posts'

    @classmethod
    def objs(cls):
        return [
            {
                "tag_id": 1,
                "post_id": 1
            },
            {
                "tag_id": 2,
                "post_id": 1
            },
            {
                "tag_id": 3,
                "post_id": 1
            },
            {
                "tag_id": 1,
                "post_id": 2
            },
            {
                "tag_id": 2,
                "post_id": 2
            },
            {
                "tag_id": 3,
                "post_id": 3
            }
        ]


class CommentSeeder(Seeder):
    @classmethod
    def wait_for(cls):
        return [
            UserSeeder,
            PostSeeder
        ]

    @classmethod
    def objs(cls):
        return [
            {
                "content": "Insightful thoughts shared here.",
                "author": 1,
                "post_id": 2
            },
            {
                "content": "I appreciate the diverse perspectives in this discussion.",
                "author": 3,
                "post_id": 1
            },
            {
                "content": "Well-articulated points. The author has a clear understanding.",
                "author": 2,
                "post_id": 3
            },
            {
                "content": "Interesting take on the topic. I hadn't considered that angle before.",
                "author": 1,
                "post_id": 1
            },
            {
                "content": "I respectfully disagree with some points mentioned.",
                "author": 2,
                "post_id": 2
            },
            {
                "content": "A great addition to the conversation. I enjoyed reading this.",
                "author": 3,
                "post_id": 3
            },
            {
                "content": "The author provides valuable insights backed by evidence.",
                "author": 1,
                "post_id": 3
            },
            {
                "content": "Thought-provoking ideas shared in this comment.",
                "author": 2,
                "post_id": 1
            },
            {
                "content": "This comment resonates with my own experiences.",
                "author": 3,
                "post_id": 2
            },
            {
                "content": "I'm intrigued by the unique perspective presented here.",
                "author": 1,
                "post_id": 1
            }
        ]


async def main():
    async with httpx.AsyncClient() as client:
        Seeder.init_client(client)
        await Seeder.seed_all()


if __name__ == '__main__':
    asyncio.run(main())
