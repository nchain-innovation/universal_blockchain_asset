import logging
from decimal import Decimal
from web3 import Web3
from web3.types import TxParams
from eth_account.datastructures import SignedTransaction
from eth_account import Account
from eth_account.signers.local import LocalAccount


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EthereumWallet:
    """ This class represents the Ethereum Wallet functionality
    """

    def __init__(self, w3: Web3, pkey: str):
        """ Initialize the EthereumWallet instance """
        # Check the pkey is not empty
        if not pkey:
            logger.error("Error: Ethereum private key is not set.")
            raise ValueError("Ethereum private key is not set.")

        self.account: LocalAccount = Account.from_key(pkey)
        self.w3: Web3 = w3

        if self.w3.is_connected():
            logger.info(f"Connected to Ethereum node at {self.w3.provider}")
        else:
            raise ConnectionError(f"Failed to connect to Ethereum node at {self.w3.provider}")

    # --------------------------------------------------------------------------------------------
    def get_balance(self) -> int:
        """ Get the balance of the account in Wei """

        # Check w3 is connected
        if not self.w3.is_connected():
            raise ConnectionError("Web3 provider is not connected")

        balance = self.w3.eth.get_balance(self.account.address)
        return balance

    # --------------------------------------------------------------------------------------------
    def get_balance_eth(self) -> int | Decimal:
        """ Get the balance of the account in ETH """

        balance_wei = self.get_balance()
        balance_eth = Web3.from_wei(balance_wei, 'ether')
        return balance_eth

    # --------------------------------------------------------------------------------------------
    def sign_transaction(self, transaction: TxParams) -> SignedTransaction:
        """Sign a transaction using the account's private key."""

        if not self.w3.is_connected():
            raise ConnectionError("Web3 provider is not connected")

        signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.account._private_key)

        return signed_txn

    # --------------------------------------------------------------------------------------------
    def is_connected(self) -> bool:
        """ Check if the web3 provider is connected """
        if self.w3 is None:
            return False
        return self.w3.is_connected()

    # --------------------------------------------------------------------------------------------
    def __repr__(self) -> str:
        """ Return a string representation of the EthereumWallet instance """
        if self.account is None:
            return 'eth account -> None'
        return f'eth account -> {self.account.address}'

    # --------------------------------------------------------------------------------------------
    def get_block_gas_limit(self) -> int:
        if self.w3 is None:
            raise ValueError("Web3 provider is not set")
        current_block = self.w3.eth.block_number
        block_gas_limit = self.w3.eth.get_block(current_block)['gasLimit']
        return block_gas_limit
