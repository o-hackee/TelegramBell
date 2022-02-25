import logging
from configparser import ConfigParser
from typing import List, Tuple

from pyrogram import Client
from pyrogram.errors import PeerIdInvalid
from pyrogram.storage import Storage
from pyrogram.storage.sqlite_storage import get_input_peer
from pyrogram.types import Message

from AlexaStorageHandler import AlexaStorageHandler

logger = logging.getLogger("lambda_function")


class PyrogramStorage(Storage):

    def __init__(self, name: str, storage_handler: AlexaStorageHandler):
        super().__init__(name)
        self.storage_handler = storage_handler

    async def open(self):
        pass

    async def save(self):
        self.storage_handler.save_to_database()

    async def close(self):
        pass

    async def delete(self):
        pass

    async def update_peers(self, peers: List[Tuple[int, int, str, str, str]]):
        """
        peers: id, access_hash, type, username, phone_number
        """
        logger.info(f"update_peers {peers}")
        stored_peers_id_to_index = {stored_peer_as_list[0]: idx for idx, stored_peer_as_list in enumerate(self.storage_handler.peers)}

        for peer in peers:
            peer_id = peer[0]
            peer_as_list = list(peer)
            if peer_id in stored_peers_id_to_index:
                self.storage_handler.peers[stored_peers_id_to_index[peer_id]] = peer_as_list
                continue
            self.storage_handler.peers.append(peer_as_list)
        self.storage_handler.save_to_database()

    async def get_peer_by_id(self, peer_id: int):
        logger.info(f"get_peer_by_id {peer_id}")
        found_peer_as_list = next(filter(lambda stored_peer_as_list: stored_peer_as_list[0] == peer_id, self.storage_handler.peers), None)
        if not found_peer_as_list:
            logger.info(f"ID not found: {peer_id}")
            raise KeyError(f"ID not found: {peer_id}")
        return get_input_peer(*found_peer_as_list[:3])

    async def get_peer_by_username(self, username: str):
        found_peer_as_list = next(filter(lambda stored_peer_as_list: stored_peer_as_list[3] == username, self.storage_handler.peers), None)
        if not found_peer_as_list:
            logger.info(f"username not found: {username}")
            raise KeyError(f"username not found: {username}")
        return get_input_peer(*found_peer_as_list[:3])

    async def get_peer_by_phone_number(self, phone_number: str):
        logger.info(f"get_peer_by_phone_number {phone_number}")
        found_peer_as_list = next(filter(lambda stored_peer_as_list: stored_peer_as_list[4] == phone_number, self.storage_handler.peers), None)
        if not found_peer_as_list:
            logger.info(f"phone_number not found: {phone_number}")
            raise KeyError(f"phone_number not found: {phone_number}")
        return get_input_peer(*found_peer_as_list[:3])

    async def dc_id(self, value: int = object):
        if isinstance(value, int):
            logger.debug(f"set dc_id {value}")
            self.storage_handler.dc_id = value
            self.storage_handler.save_to_database()
        logger.debug(f"get dc_id {self.storage_handler.dc_id}")
        return self.storage_handler.dc_id

    async def test_mode(self, value: bool = object):
        if isinstance(value, bool):
            logger.debug(f"set test_mode {value}")
            self.storage_handler.test_mode = value
            self.storage_handler.save_to_database()
        logger.debug(f"get test_mode {self.storage_handler.test_mode}")
        return self.storage_handler.test_mode

    async def auth_key(self, value: bytes = object):
        if isinstance(value, bytes):
            logger.debug(f"set auth_key {value}")
            self.storage_handler.auth_key = value
            self.storage_handler.save_to_database()
        logger.debug(f"get auth_key {self.storage_handler.auth_key}")
        return self.storage_handler.auth_key

    async def date(self, value: int = object):
        if isinstance(value, int):
            logger.debug(f"set date {value}")
            self.storage_handler.date = value
            self.storage_handler.save_to_database()
        logger.debug(f"get date {self.storage_handler.date}")
        return self.storage_handler.date

    async def user_id(self, value: int = object):
        if isinstance(value, int):
            logger.debug(f"set user_id {value}")
            self.storage_handler.user_id = value
            self.storage_handler.save_to_database()
        logger.debug(f"get user_id {self.storage_handler.user_id}")
        return self.storage_handler.user_id

    async def is_bot(self, value: bool = object):
        if isinstance(value, bool):
            logger.debug(f"set is_bot {value}")
            self.storage_handler.is_bot = value
            self.storage_handler.save_to_database()
        logger.debug(f"get is_bot {self.storage_handler.is_bot}")
        return self.storage_handler.is_bot


def read_recipient(config_file):
    parser = ConfigParser()
    parser.read(str(config_file))

    return parser.get("custom", "recipient", fallback="me")


class PyrogramClient:

    def __init__(self, storage_handler: AlexaStorageHandler):
        config_file = "pyrogram_config.ini"
        self.client = Client(PyrogramStorage("alexa_storage", storage_handler), config_file=config_file)
        self.recipient = read_recipient(config_file)
        self._is_authorized = self.client.connect()
        logger.info(f"PyrogramManager created, is_authorized={self._is_authorized}")

    def get_is_authorized(self):
        return self._is_authorized

    def send_code(self, phone_number):
        logger.info("PyrogramManager send_code")
        result = self.client.send_code(phone_number)
        return result.phone_code_hash

    def sign_in(self, phone_number, phone_code_hash, code):
        logger.info("PyrogramManager sign_in")
        result = self.client.sign_in(phone_number, phone_code_hash, str(code))
        return result

    def send_message(self, message: str) -> bool:
        logger.info("PyrogramManager send_message")
        try:
            ret = self.client.send_message(chat_id=self.recipient, text=message)
        except PeerIdInvalid:
            logger.info(f"caught invalid peer exception for {self.recipient}")
            # assuming a phone number was provided (username should be handled), fetch the contacts
            # (flaw: the contacts won't be updated automatically by every usage unless the exception happens again -
            # and might become stail)
            contacts = self.client.get_contacts()
            # logger.info(f"contacts {contacts}")
            ret = self.client.send_message(chat_id=self.recipient, text=message)
        return isinstance(ret, Message)
