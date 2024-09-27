from typing import Any, Dict, Optional

import sys
sys.path.append("..")

from config import ConfigType

from service.commitment_packet import Cpid
from web3 import Web3
from ethereum.ethereum_wallet import EthereumWallet

"""from web3_py.erc20 import ERC20
from web3_py.raw_transaction import RawTransaction
"""
from web3_py.smart_contract import SmartContract


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
        self.web3 = Web3(Web3.HTTPProvider(config["ethereum_service"]["ethNodeUrl"] + config["ethereum_service"]["apiKey"]))
        self.eth_type = config["ethereum_service"]["interface_type"]
        if self.eth_type == "SmartContract":
            self.eth_interface = SmartContract(config, self.web3)
        elif self.eth_type == "RawTransaction":
            raise NotImplementedError
        elif self.eth_type == "ERC20":
            raise NotImplementedError

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
        return self.eth_interface.create_ownership(wallet)

    def spend_ownership_tx(self, txid: str, wallet: EthereumWallet, cpid: Cpid) -> str:
        """ Given a reference to a transaction, spend it or
            return None if failed
        """
        return self.eth_interface.spend_ownership(txid, cpid, wallet)
