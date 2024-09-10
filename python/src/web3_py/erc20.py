from web3_py.ethereum_interface import EthereumInterface
import json


class ERC20(EthereumInterface):
    def __init__(self, ethNodeUrl, apiKey, privateKey, gas, gasPrice, config):
        super().__init__(ethNodeUrl, apiKey, privateKey, gas, gasPrice)

        print("ERC20 constructor")

        # read from the config file to get abi_filename and bytecode_filename
        required_fields = ['abi_filename', 'bytecode_filename']
        if not all(field in config for field in required_fields):
            missing_fields = [field for field in required_fields if field not in config]
            raise ValueError(f"Missing required fields in configuration: {', '.join(missing_fields)}")

        abi_filename = config['abi_filename']
        bytecode_filename = config['bytecode_filename']
        self.abi = self._load_abi(abi_filename)
        self.bytecode = self._load_bytecode(bytecode_filename)
        self.contract_address = None

    def _load_abi(self, filename):
        try:
            with open(filename) as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File {filename} not found.")
            raise FileNotFoundError(f"File {filename} not found.")

    def _load_bytecode(self, filename):
        try:
            with open(filename) as f:
                return f.read()
        except FileNotFoundError:
            print(f"File {filename} not found.")
            raise FileNotFoundError(f"File {filename} not found.")

    # This is the ERC20 token minting function
    def create_ownership(self):
        print("create_ownership")
        # Set up the contract
        contract = self.web3.eth.contract(abi=self.abi, bytecode=self.bytecode)
        # Get the nonce
        nonce = self.web3.eth.get_transaction_count(self.account.address)
        # Build a transaction
        transaction = {
            'nonce': nonce,
            'gas': self.gas,
            'gasPrice': self.web3.to_wei(self.gasPrice, 'gwei'),
        }
        # Get the contract deployment
        contract_txn = contract.constructor().build_transaction(transaction)

        # Sign the transaction
        # signed_txn = self.web3.eth.account.sign_transaction(contract_txn, private_key=self.privateKey)
        signed_txn = self.account.sign_transaction(contract_txn)

        # Send the transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash_hex = tx_hash.hex()

        # Get the transaction receipt
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        # Get the contract address from the transaction receipt
        self.contract_address = tx_receipt['contractAddress']
        print(f"Token created. Contract deployed at {self.contract_address}")
        return tx_hash_hex, self.contract_address

    # This is the ERC20 token burning function
    def spend_ownership(self, txid: str, CPID: str):
        # <TODO> Record the CPID
        print("Spending ownership:  TXID not used,, CPID not recorded <TODO>")

        if self.contract_address is None:
            raise ValueError("Contract address not set. Call create_ownership() first.")

        # Set up the contract using the saved contract address
        contract = self.web3.eth.contract(address=self.contract_address, abi=self.abi)

        # Get the nonce
        nonce = self.web3.eth.get_transaction_count(self.account.address)
        print(f"Nonce: {nonce}")

        # Build a transaction
        txn = contract.functions.burn().build_transaction({
            'gas': self.gas,
            'gasPrice': self.web3.to_wei(self.gasPrice, 'gwei'),
            'nonce': nonce,
        })

        # Sign the transaction
        # signed_txn = self.web3.eth.account.sign_transaction(txn, private_key=self.privateKey)
        signed_txn = self.account.sign_transaction(txn)

        # Send the transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        print(f"tx_hash: {tx_hash_hex}")

        # Get the transaction receipt
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Token burned, transaction hash: {tx_hash.hex()}")
        print("Transaction receipt:", tx_receipt)
        return tx_hash.hex()

    # This function checks if the token has been burnt
    def tx_spent_status(self, tx_hash: str):
        # Get the transaction receipt
        tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)

        # Check if the transaction was successful
        if tx_receipt['status'] == 1:
            print("The token has been burnt.")
        else:
            print("The token has not been burnt.")

    # OR should this be done differently?  Because checking the last transaction status may not be enough
    # what if the transaction is not a "burning" transaction but some other transaction?
            # use the txid to get the contract

            # use the ABI?

            # check the owner's balance (should be 1 Ether) using balanceOf

            #  if 1, return True, else False

# --------------------------------------------------------------------------------------------
    # check the ownership by determining if the token has been burned
    # can do this by checking the balanceOf the owner
    # def check_ownership(self, txid):
