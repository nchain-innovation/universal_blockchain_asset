import requests
import logging
import json
import time
from packaging import version
from typing import Any, Dict
from config import ConfigType

LOGGER = logging.getLogger(__name__)


class FinancingServiceException(Exception):
    pass


class FinancingService:
    """ This class represents the Financing Service interface
    """
    def __init__(self):
        self.service_url: str
        self.client_id: str
        self.utxo_cache_enabled: bool
        self.utxo_persistence_enabled: bool
        self.utxo_file: str
        self.utxo_min_level: int
        self.utxo_request_level: int
        self.utxo = {}

    def set_config(self, config: ConfigType):
        """ Given the configuration, configure this service"""
        self.service_url = config["finance_service"]["url"]
        self.client_id = config["finance_service"]["client_id"]
        # cache stuff
        self.utxo_cache_enabled = config["finance_service"]["utxo_cache_enabled"]
        self.utxo_persistence_enabled = config["finance_service"]["utxo_persistence_enabled"]
        self.utxo_file = config["finance_service"]["utxo_file"]
        self.utxo_min_level = config["finance_service"]["utxo_min_level"]
        self.utxo_request_level = config["finance_service"]["utxo_request_level"]
        # if configured load utxo
        if self.utxo_cache_enabled:
            self.load_utxo()

    def _check_version(self, data: Dict[str, Any]):
        """ Throw exception if Financing service is version is below MIN_VERSION
        """
        MIN_VERSION = "0.2.0"
        try:
            finance_service_version = data['version']
        except KeyError:
            raise FinancingServiceException(f"Unable to get version from finance service. Check that the finance service is version '{MIN_VERSION}' or above.")
        else:
            # Must be 0.2.0 or above - to return funding tx with txid
            min_version = version.parse(MIN_VERSION)
            if version.parse(finance_service_version) < min_version:
                raise FinancingServiceException(f"the finance service is version '{finance_service_version}', it should be '{MIN_VERSION}' or above.")

    def get_status(self) -> None | Dict[str, Any]:
        """ Return the status of the funding service
        """
        data = None
        try:
            response = requests.get(self.service_url + "/status", timeout=1.0)
        except:
            raise FinancingServiceException("ConnectionError connecting to finance service. Check that the finance service is running.")
        else:
            if response.status_code == 200:
                data = response.json()
                LOGGER.debug(f"data = {data}")
                self._check_version(data)
            else:
                LOGGER.debug(f"response = {response}")
        return data

    def get_balance(self) -> None | Dict[str, Any]:
        """ Return the balance for our client_id
        """
        data = None
        id = self.client_id
        try:
            response = requests.get(self.service_url + f"/balance/{id}")
        except:
            raise FinancingServiceException("ConnectionError connecting to finance service. Check that the finance service is running.")
        else:
            if response.status_code == 200:
                data = response.json()
                LOGGER.debug(f"data = {data}")
            else:
                LOGGER.debug(f"response = {response}")
        return data

    def get_funds(self, fee_estimate: int, locking_script: str) -> None | Dict[str, Any]:
        """ Get the funds for one tx
        """
        if self.utxo_cache_enabled:
            # if below the threshold get more tx in the cache
            if locking_script in self.utxo:
                if len(self.utxo[locking_script]) < self.utxo_min_level:
                    result = self._get_funds(fee_estimate, locking_script, self.utxo_request_level, False)
                    if result is None:
                        return None
                    else:
                        # add them to the cache
                        assert result["status"] == "Success"
                        self.utxo[locking_script].extend(result["outpoints"])
            else:
                result = self._get_funds(fee_estimate, locking_script, self.utxo_request_level, False)
                if result is None:
                    return None
                else:
                    # add them to the cache
                    assert result["status"] == "Success"
                    if locking_script not in self.utxo:
                        self.utxo[locking_script] = []
                    self.utxo[locking_script].extend(result["outpoints"])
            # Pop outpoint off the cache
            utxo = self.utxo[locking_script].pop()
            # Save utxo
            self.save_utxo()
            return {"status": "Success", "outpoints": [utxo]}
        else:
            return self._get_funds(fee_estimate, locking_script, 1, False)

    def _get_funds(self, fee_estimate: int, locking_script: str, no_of_outpoints: int, multiple_tx: bool) -> None | Dict[str, Any]:
        """ Underlying get_funds call
        """
        # Convert to lower case string for url
        mult_tx = "true" if multiple_tx else "false"
        id = self.client_id
        url = self.service_url + f"/fund/{id}/{fee_estimate}/{no_of_outpoints}/{mult_tx}/{locking_script}"
        response = requests.post(url)
        data = None
        if response.status_code == 200:
            data = response.json()
            LOGGER.debug(f"data = {data}")
            # Delay so that we can see the transaction
            time.sleep(0.5)
        else:
            LOGGER.debug(f"response = {response}")
        return data

    def load_utxo(self):
        if self.utxo_persistence_enabled:
            try:
                with open(self.utxo_file, 'r') as f:
                    self.utxo = json.load(f)
            except FileNotFoundError:
                pass

    def save_utxo(self):
        if self.utxo_persistence_enabled:
            # Convert to something we can write out
            with open(self.utxo_file, 'w') as f:
                json.dump(self.utxo, f)

    def cache_enabled(self) -> bool:
        return self.utxo_cache_enabled

    def cache_size(self) -> int:
        sz = 0
        if self.utxo_cache_enabled:
            for v in self.utxo.values():
                sz += len(v)
        return sz
