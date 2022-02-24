from typing import List, Tuple

from pyrogram.storage import Storage


class AlexaStorage(Storage):

    async def open(self):
        pass

    async def save(self):
        pass

    async def close(self):
        pass

    async def delete(self):
        pass

    async def update_peers(self, peers: List[Tuple[int, int, str, str, str]]):
        pass

    async def get_peer_by_id(self, peer_id: int):
        pass

    async def get_peer_by_username(self, username: str):
        pass

    async def get_peer_by_phone_number(self, phone_number: str):
        pass

    async def dc_id(self, value: int = object):
        pass

    async def test_mode(self, value: bool = object):
        pass

    async def auth_key(self, value: bytes = object):
        pass

    async def date(self, value: int = object):
        pass

    async def user_id(self, value: int = object):
        pass

    async def is_bot(self, value: bool = object):
        pass

    def __init__(self, name: str):
        super().__init__(name)
