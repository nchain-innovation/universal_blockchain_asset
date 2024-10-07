import requests
import logging
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

    def set_config(self, config: ConfigType):
        """ Given the configuration, configure this service"""
        self.service_url = config["finance_service"]["url"]
        self.client_id = config["finance_service"]["client_id"]

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
