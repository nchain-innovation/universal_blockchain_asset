from typing import Any, Dict, Optional, Tuple

import sys
sys.path.append("..")

from config import ConfigType
from service.commitment_packet import Cpid
from web3 import Web3
from ethereum.ethereum_wallet import EthereumWallet
from web3_py.smart_contract import SmartContract
import logging

logger = logging.getLogger(__name__)


class EthereumService:
    """ This captures the Ethereum interface
    """
    def __init__(self):
        self.eth_type: str
        self.eth_interface: Any
        self.web3: Web3

    def set_config(self, config: ConfigType):
        """ Given the configuration, configure the service
        """
        self.eth_node_url = config["ethereum_service"]["ethNodeUrl"]
        self.api_key = config["ethereum_service"]["apiKey"]
        self.web3 = Web3(Web3.HTTPProvider(self.eth_node_url + self.api_key))

        self.eth_type = config["ethereum_service"]["interface_type"]

        if self.eth_type == "SmartContract":

            interface_config = None
            for obj in config["interface"]:
                if obj["name"] == "SmartContract":
                    interface_config = obj
                    break

            if interface_config is None:
                raise ValueError("SmartContract interface configuration not found")

            self.eth_interface = SmartContract(interface_config, self.web3)

        elif self.eth_type == "RawTransaction":
            raise NotImplementedError
        elif self.eth_type == "ERC20":
            raise NotImplementedError
        else:
            raise ValueError("Invalid Ethereum interface type")

    def is_connected(self) -> bool:
        """ Return True if the Ethereum interface is connected
        """
        return self.web3.is_connected()

    def reconnect(self):
        """ Attempt to reconnect to the Ethereum node
        """
        logger.info("Attempting to reconnect to the Ethereum node...")
        self.web3 = Web3(Web3.HTTPProvider(self.eth_node_url + self.api_key))

        if self.web3.is_connected():
            logger.info("Reconnected to the Ethereum node successfully.")
        else:
            logger.error("Failed to reconnect to the Ethereum node.")

    def get_status(self) -> None | Optional[Dict[str, Any]]:
        """ Return the status of the Ethereum interface, so that we know if it is connected
            return dictionary of information if present
            and None if connection failed
        """
        if self.web3.is_connected():
            return {
                "status": "connected",
                "network_id": self.web3.net.version,
                "latest_block": self.web3.eth.block_number
            }
        else:
            return None

    def is_ownership_tx_spent(self, txid: str) -> None | bool:
        """ Given an tx reference return true if it has been spent
            Return None on failure
        """
        return False

    def create_ownership_tx(self, wallet: EthereumWallet) -> str:
        """ Given a wallet create an ownership transaction and return a reference to it
            that can be used to spend it later or determine if it has been spent
        """
        if not self.web3.is_connected():
            self.reconnect()
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to the Ethereum node.")
            else:
                logger.info("Reconnected to the Ethereum node successfully.")
                self.eth_interface.set_web3(self.web3)

        return self.eth_interface.create_ownership(wallet)

    def spend_ownership_tx(self, txid: str, wallet: EthereumWallet, cpid: str) -> str:
        """ Given a reference to a transaction, spend it or
            return None if failed
        """
        if not self.web3.is_connected():
            self.reconnect()
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to the Ethereum node.")
            else:
                logger.info("Reconnected to the Ethereum node successfully.")
                self.eth_interface.set_web3(self.web3)

        return self.eth_interface.spend_ownership(txid, cpid, wallet)

    def get_cpid_from_txid(self, txid: str) -> Cpid:
        """ Given a transaction reference return the CPID
        """
        if not self.web3.is_connected():
            self.reconnect()
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to the Ethereum node.")
            else:
                logger.info("Reconnected to the Ethereum node successfully.")
                self.eth_interface.set_web3(self.web3)

        return self.eth_interface.get_cpid(txid)

    def get_tx_spent_status(self, txid: str) -> bool:
        """ Given a transaction reference return if it has been spent
        """
        if not self.web3.is_connected():
            self.reconnect()
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to the Ethereum node.")
            else:
                logger.info("Reconnected to the Ethereum node successfully.")
                self.eth_interface.set_web3(self.web3)

        return self.eth_interface.tx_spent_status(txid)

    def get_event_and_utxo(self, txid: str) -> Tuple[str, str]:
        """ Given a transaction reference return the event and utxo
        """
        if not self.web3.is_connected():
            self.reconnect()
            if not self.web3.is_connected():
                raise ConnectionError("Failed to connect to the Ethereum node.")
            else:
                logger.info("Reconnected to the Ethereum node successfully.")
                self.eth_interface.set_web3(self.web3)

        return self.eth_interface.get_event_and_utxo(txid)
