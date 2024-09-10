from abc import ABC, abstractmethod
from web3 import Web3, Account


class EthereumInterface(ABC):
    def __init__(self, ethNodeUrl, apiKey, privateKey, gas, gasPrice):
        self.ethNodeUrl = ethNodeUrl
        self.apiKey = apiKey
        self.account = Account.from_key(privateKey)
        self.gas = gas
        self.gasPrice = gasPrice
        self.web3 = Web3(Web3.HTTPProvider(self.ethNodeUrl + self.apiKey))
        print(f"EthNodeUrl: {self.ethNodeUrl} is connected: {self.web3.is_connected()}")

    def is_connected(self):
        return self.web3.is_connected()

    @abstractmethod
    def create_ownership(self):
        pass

    @abstractmethod
    def spend_ownership(self, tx_hash: str, CPID: str):
        pass

    @abstractmethod
    def tx_spent_status(self, tx_hash):
        pass

    # --------------------------------------------------------------------------------------------
    # Check the balance of the account in Ether
    def check_balance(self):
        if self.web3 is None:
            raise Exception("Not connected. Call connect() first.")

        print(f"Account: {self.account.address}")
        balance = self.web3.eth.get_balance(self.account.address)
        balance_in_ether = self.web3.from_wei(balance, 'ether')
        return balance_in_ether

    # --------------------------------------------------------------------------------------------
    # Check if the account has sufficient funds for a transaction and its gas fees
    def check_funds(self, amount):
        print("in check_funds")

        gas_limit = self.gas
        gas_price = self.web3.to_wei(self.gasPrice, 'gwei')
        # Check the types of the arguments
        if not isinstance(amount, (int, float, str)):
            raise TypeError("Unsupported type for 'amount'. Must be one of integer, float, or string")
        if not isinstance(gas_limit, int):
            raise TypeError("Unsupported type for 'gas_limit'. Must be an integer")
        if not isinstance(gas_price, int):
            raise TypeError("Unsupported type for 'gas_price'. Must be an integer")

        print("after type check")

        # Convert the amount to Wei (the smallest unit of Ether)
        amount_wei = self.web3.to_wei(amount, 'ether')

        # Calculate the total cost of the transaction (amount + gas fees)
        total_cost = amount_wei + gas_limit * gas_price

        # Get the account balance
        balance = self.web3.eth.get_balance(self.account.address)

        print(f"Account balance: {balance}")
        print(f"Total cost: {total_cost}")
        # Check if the balance is greater than or equal to the total cost
        return balance >= total_cost
