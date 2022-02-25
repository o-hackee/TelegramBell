from decimal import Decimal

from ask_sdk_core.attributes_manager import AttributesManager
from boto3.dynamodb.types import Binary


class AlexaStorageHandler:
    def __init__(self, attributes_manager: AttributesManager):
        self.attributes_manager = attributes_manager
        persistent_attributes = attributes_manager.persistent_attributes
        self.peers = persistent_attributes.get("peers", [])
        self.dc_id = persistent_attributes.get("dc_id", 0)
        self.test_mode = persistent_attributes.get("test_mode")
        self.auth_key = persistent_attributes.get("auth_key")
        self.date = persistent_attributes.get("date")
        self.user_id = persistent_attributes.get("user_id", 0)
        self.is_bot = persistent_attributes.get("is_bot", False)

        self._cast_to_native_python_types()

    def _cast_to_native_python_types(self):
        """
        When we receive data from DynamoDB, we don't get native Python types. However, other libraries (e.g.: Pyrogram)
        work only with native Python types. Therefore, we need to cast it.
        """
        if isinstance(self.dc_id, Decimal):
            self.dc_id = int(self.dc_id)
        if isinstance(self.user_id, Decimal):
            self.user_id = int(self.user_id)

        if isinstance(self.auth_key, Binary):
            self.auth_key = self.auth_key.value

        for peer_as_list in self.peers:
            for idx, element in enumerate(peer_as_list):
                if isinstance(element, Decimal):
                    peer_as_list[idx] = int(peer_as_list[idx])

    def to_dict(self):
        return {
            "peers": self.peers,
            "dc_id": self.dc_id,
            "test_mode": self.test_mode,
            "auth_key": self.auth_key,
            "date": self.date,
            "user_id": self.user_id,
            "is_bot": self.is_bot,
        }

    def save_to_database(self):
        self.attributes_manager.persistent_attributes = self.to_dict()
        self.attributes_manager.save_persistent_attributes()
