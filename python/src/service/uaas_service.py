import requests

from typing import Any, Dict

import sys
sys.path.append("..")

from config import ConfigType


class UaaSException(Exception):
    pass


class UaaSService:
    """ This class represents the a UTXO Client interface
    """

    def __init__(self):
        self.service_url: str
        self.collection: str

    def set_config(self, config: ConfigType):
        """ Given the configuration, configure the client
        """
        self.service_url = config["uaas"]["service_url"]
        self.collection = config["uaas"]["collections"]

    def get_status(self) -> None | Dict[str, Any]:
        """ Return the status of the funding service
        """
        data = None
        try:
            response = requests.get(self.service_url + "/status", timeout=1.0)
        except:
            raise UaaSException("ConnectionError connecting UaaS. Check that the service is running.")
        else:
            if response.status_code == 200:
                data = response.json()
            else:
                raise UaaSException(f"ConnectionError connecting UaaS. response = {response}")
        return data

    def get_collection_parsed_tx(self, collection: str, txid: str) -> None | Dict[str, Any]:
        endpoint = f"/collection/tx/parsed?cname={collection}&hash={txid}"
        response = None
        try:
            response = requests.get(self.service_url + endpoint, timeout=1.0)
        except:
            if response is not None:
                print(f"response = {response}")
            return None
        else:
            if response.status_code == 200:
                data = response.json()
            else:
                print(f"ConnectionError connecting UaaS. response = {response}")
                return None
        return data

    def has_outpoint_been_spent(self, txid: str, index: int) -> None | bool:
        assert len(self.collection) == 1
        collection = self.collection[0]
        result = self.get_collection_parsed_tx(collection, txid)
        if result is None:
            return None
        try:
            retval = result['tx']['vout'][index]['spent']
        except KeyError as e:
            print(f"has_outpoint_been_spent - KeyError {e}")
            return None
        return retval


if __name__ == '__main__':
    us = UaaSService()
    CONFIG = {
        "uaas": {
            "service_url": "http://host.docker.internal:5010",
            "collections": ["commitment"],
        },
    }
    us.set_config(CONFIG)
    result = us.get_status()
    print(result)
    us.has_outpoint_been_spent("d05ccc81d389023e94e4ee5123b8c19bdf6f031daafb1cb64adc8be0490bc1b8", 1)
