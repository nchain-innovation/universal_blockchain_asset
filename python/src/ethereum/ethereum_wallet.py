import sys
sys.path.append("..")


from config import ConfigType
from web3 import Web3, Account


class EthereumWallet:
    """ This class represents the Ethereum Wallet functionality
    """
    def __init__(self):
        self.account: Account
        self.ethNodeUrl: str
        self.apiKey: str
        self.gas: str
        self.gasPrice: str
        self.maxGasPrice: str
        self.web3: Web3

    def set_config(self, config: ConfigType):
        ethereum_config = config["ethereum_service"]
        """ Given the wallet configuration, set up the wallet"""
        self.ethNodeUrl = ethereum_config["ethNodeUrl"]
        self.apiKey = ethereum_config["apiKey"]
        self.gas = ethereum_config["gas"]
        self.gasPrice = ethereum_config["gasPrice"]
        self.maxGasPrice = ethereum_config["maxGasPrice"]
        self.web3 = Web3(Web3.HTTPProvider(self.ethNodeUrl + self.apiKey))
        print(f"EthNodeUrl: {self.ethNodeUrl} is connected: {self.web3.is_connected()}")
        block_gas_limit = self.get_block_gas_limit()

        # self.gas = min(self.gas, block_gas_limit)
        print(f"JAS: DEBUG: Gas limit: {self.gas}, Block gas limit: {block_gas_limit}")

    def set_account(self, eth_key: str):
        self.account = Account.from_key(eth_key)

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
    def check_funds(self, gas_estimate):
        print("in check_funds")

        # gas_limit = self.gas
        gas_price = self.web3.to_wei(self.gasPrice, 'gwei')
        # Check the types of the arguments
        if not isinstance(gas_estimate, (int, float, str)):
            raise TypeError("Unsupported type for 'gas_estimate'. Must be one of integer, float, or string")
        # if not isinstance(gas_limit, int):
        #     raise TypeError("Unsupported type for 'gas_limit'. Must be an integer")
        if not isinstance(gas_price, int):
            raise TypeError("Unsupported type for 'gas_price'. Must be an integer")

        print("after type check")

        # Convert the amount to Wei (the smallest unit of Ether)
        # amount_wei = self.web3.to_wei(gas_estimate, 'ether')

        # Calculate the total cost of the transaction
        total_cost = gas_estimate * gas_price

        # Get the account balance
        balance = self.web3.eth.get_balance(self.account.address)

        print(f"Account balance: {balance}")
        print(f"Estimated cost: {total_cost}")
        # Check if the balance is greater than or equal to the total cost
        return balance >= total_cost

    def is_connected(self):
        return self.web3.is_connected()

    def __repr__(self) -> str:
        return ''.join(f'eth account -> {self.account.address}')

    def get_block_gas_limit(self):
        current_block = self.web3.eth.block_number
        block_gas_limit = self.web3.eth.get_block(current_block)['gasLimit']
        print(f"JAS: DEBUG: Current block gas limit: {block_gas_limit}")
        return block_gas_limit

    def update_gas_price(self, num_transactions=10):
        # Get the latest block number
        latest_block = self.web3.eth.block_number

        # Collect gas prices from the last `num_transactions` transactions
        gas_prices = []
        for i in range(num_transactions):
            block = self.web3.eth.get_block(latest_block - i)
            if not block['transactions']:
                print(f"Block {latest_block - i} has no transactions. Skipping...")
                continue
            tx_hash = block['transactions'][0]
            tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            if tx_receipt['effectiveGasPrice'] is None:
                print(f"Transaction {tx_hash} is pending. Skipping...")
                continue  # Skip this iteration if effectiveGasPrice is None
            last_gas_price = int(self.web3.from_wei(tx_receipt['effectiveGasPrice'], 'gwei'))
            print(f"Transaction {tx_hash.hex()} has gas price: {last_gas_price}")
            gas_prices.append(last_gas_price)

        # Calculate the average gas price
        if gas_prices:
            print(f"initial gas price: {self.gasPrice}")

            print(f"Gas prices: {gas_prices}")
            print(f"Sum of gas prices: {sum(gas_prices)}")
            print(f"Number of transactions: {len(gas_prices)}")
            average_gas_price = int(sum(gas_prices) / len(gas_prices))
            print(f"Average gas price: {average_gas_price}")

            if average_gas_price < self.maxGasPrice:
                print(f"Updating gas price from {self.gasPrice} to {average_gas_price}")
                self.gasPrice = average_gas_price
                return True
            else:
                print(f"Average gas price exceeds the maximum allowed value of {self.maxGasPrice}.")
                print("Gas price remains unchanged.")
                raise Exception(f"Average gas price of {average_gas_price} exceeds the maximum allowed value of {self.maxGasPrice}.")

        else:
            print("No transactions found, gas price remains unchanged.")
            return False  # Return None if no transactions were found or processed
