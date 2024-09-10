from web3 import exceptions, Web3
from eth_account import Account
from ethereum.ethereum_wallet import EthereumWallet

from config import ConfigType
import json
import warnings


class SmartContract:
    def __init__(self, config: ConfigType, web3: Web3):
        assert config["ethereum_service"]["interface_type"] == "SmartContract"
        self.web3 = web3

        interface_confg = None
        for obj in config["interface"]:
            if obj["name"] == "SmartContract":
                interface_confg = obj

        # Read from the config file to get abi_filename and bytecode_filename, and contract owner
        required_fields = ['abi_filename', 'bytecode_filename', 'contract_pkey', 'contract_deployment']
        # print(interface_confg)
        if not all(field in interface_confg for field in required_fields):
            missing_fields = [field for field in required_fields if field not in interface_confg]
            raise ValueError(f"Missing required fields in configuration: {', '.join(missing_fields)}")

        abi_filename = interface_confg['abi_filename']
        bytecode_filename = interface_confg['bytecode_filename']
        self.abi = self._load_abi(abi_filename)
        self.bytecode = self._load_bytecode(bytecode_filename)

        self.contract_deployment = interface_confg['contract_deployment']
        if interface_confg['contract_pkey'] == "":
            print("Contract owner private key not found in config")
        else:
            self.contract_account = Account.from_key(interface_confg['contract_pkey'])

        if self.contract_deployment == "":
            self._deploy_contract()
        else:
            self._load_contract()

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

    def _deploy_contract(self):
        print("Deploying contract")

        # Estimate the gas required to deploy the contract
        contract = self.web3.eth.contract(abi=self.abi, bytecode=self.bytecode)
        gas_estimate = contract.constructor().estimate_gas()

        # Get current balance of the contract account
        balance = self.web3.eth.get_balance(self.contract_account.address)
        print(f"Balance: {balance}, Gas estimate: {gas_estimate}")

        # Deploy the contract
        if gas_estimate < balance:

            # Get the nonce
            nonce = self.web3.eth.get_transaction_count(self.contract_account.address)

            # Build a transaction
            # <TODO> These need to come from the contract owner - not done yet
            transaction = {
                'nonce': nonce,
                'gas': self.gas,  # won't work - do contract_owner_wallet.gas and .gasPrice
                'gasPrice': self.web3.to_wei(self.gasPrice, 'gwei'),
            }
            # Get the contract deployment
            contract_txn = contract.constructor().build_transaction(transaction)
            # Sign the transaction
            signed_txn = self.contract_account.sign_transaction(contract_txn)
            # Send the transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            print(f"tx_hash: {tx_hash_hex}")
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            self.contract_deployment = tx_receipt['contractAddress']
            print(f"Contract deployed at address: {self.contract_deployment}")
            # Create and store the contract instance
            self.contract = self.web3.eth.contract(address=self.contract_deployment, abi=self.abi)
        else:
            raise Exception(f"Insufficient funds to deploy contract, gas estimate: {gas_estimate}, balance: {balance}")

    def _load_contract(self):
        print(f"Loading contract from: {self.contract_deployment} ")
        self.contract = self.web3.eth.contract(address=self.contract_deployment, abi=self.abi)

    def _txhash_to_utxoid(self, tx_hash):
        print(f"Converting tx_hash to UTXO ID, tx_hash: {tx_hash}")
        # Get the transaction receipt
        tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)

        # Get the contract instance
        if self.contract is None:
            self.contract = self.web3.eth.contract(address=self.contract.address, abi=self.contract.abi)

        # Parse the logs
        logs = self.contract.events.UTXOCreated().process_receipt(tx_receipt)

        # Get the TXID from the logs
        if logs:
            print("Logs found")
            utxo = logs[0]['args']['utxoId']
            utxo_id_hex = utxo.hex()
            print(f"UTXO ID: {utxo_id_hex}")

        else:
            print("No logs found")
            raise Exception("No logs found")

        return utxo

    def create_ownership(self, wallet: EthereumWallet) -> str:
        print("Creating ownership")
        # Estimate the gas required to call createUTXO
        gas_estimate = self.contract.functions.createUTXO().estimate_gas()
        balance = self.web3.eth.get_balance(wallet.account.address)
        print(f"Gas estimate: {gas_estimate}, balance: {balance}")

        # check the funds will cover is
        wallet.check_funds(gas_estimate)
        # if wallet.update_gas_price() and gas_estimate < balance:
        if gas_estimate < balance:
            transaction = self.contract.functions.createUTXO().build_transaction({
                'from': wallet.account.address,
                'gas': wallet.gas,
                'gasPrice': self.web3.to_wei(wallet.gasPrice, 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(wallet.account.address),
            })

            # signed_txn = self.web3.eth.account.sign_transaction(transaction, self.privateKey)
            signed_txn = wallet.account.sign_transaction(transaction)

            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Transaction hash: {tx_hash.hex()}")

            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            print("Transaction receipt:", tx_receipt)
            # Check the status
            if tx_receipt['status'] == 0:
                raise Exception("Transaction failed, status is 0")

            return tx_hash.hex()

        else:
            print(f"Gas estimate to call createUTXO is too high: {gas_estimate}")
            raise Exception(f"Gas estimate to call createUTXO is too high: {gas_estimate}, balance: {balance}")

    def spend_ownership(self, tx_hash, cpid, wallet: EthereumWallet):
        print(f"Spending ownership, tx_hash: {tx_hash}, CPID: {cpid}")
        utxo = None
        try:
            utxo = self._txhash_to_utxoid(tx_hash)
        except Exception as e:
            print(e)
            raise Exception(f"Error converting tx_hash to UTXO ID, tx_hash: {tx_hash}, error: {e}")

        if utxo is None:
            raise Exception("UTXO ID not found")

        try:
            gas_estimate = self.contract.functions.spendUTXO(utxo, cpid).estimate_gas({
                'from': wallet.account.address,
            })
        except exceptions.ContractLogicError as e:
            print("Transaction would fail with message: ", e)
            raise Exception(e.args[0])
        balance = self.web3.eth.get_balance(wallet.account.address)
        # Call spendUTXO
        # if wallet.update_gas_price() and gas_estimate < balance:
        print(f'Gas estimate in smartcontract.py -> {gas_estimate}')
        if gas_estimate < balance:

            transaction = self.contract.functions.spendUTXO(utxo, cpid).build_transaction({
                'from': wallet.account.address,
                'gas': wallet.gas,
                'gasPrice': self.web3.to_wei(wallet.gasPrice, 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(wallet.account.address),
            })

            # signed_txn = self.web3.eth.account.sign_transaction(transaction, self.privateKey)
            signed_txn = wallet.account.sign_transaction(transaction)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

            # Check the status
            if tx_receipt['status'] == 0:
                raise Exception("Transaction failed, status is 0")
            return tx_hash.hex()
        else:
            print(f"Gas estimate to call spendUTXO is too high: {gas_estimate}")
            raise Exception(f"Gas estimate to call spendUTXO is too high: {gas_estimate}, balance: {balance}")

    def tx_spent_status(self, tx_hash):
        utxo = None
        try:
            utxo = self._txhash_to_utxoid(tx_hash)
        except Exception as e:
            raise Exception(f"Error converting tx_hash to UTXO ID, tx_hash: {tx_hash}, error: {e}")

        if utxo is None:
            raise Exception("UTXO ID not found")
        # Call isUTXOSpent
        return self.contract.functions.isUTXOSpent(utxo).call()

    def get_cpid(self, tx_hash):
        print(f"Getting CPID for tx_hash: {tx_hash}")
        utxo = None
        try:
            utxo = self._txhash_to_utxoid(tx_hash)
        except Exception as e:
            raise Exception(f"Error converting tx_hash to UTXO ID, tx_hash: {tx_hash}, error: {e}")

        if utxo is None:
            raise Exception("UTXO ID not found")
        # Call getUTXOCPID
        cpid = self.contract.functions.getCpid(utxo).call()
        return cpid

    def get_event_and_utxo(self, tx_hash):
        print(f"Getting event and UTXO for tx_hash: {tx_hash}")
        # Suppress the UserWarning
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning)

            # Get the transaction receipt
            tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)

            # Get the contract instance
            if self.contract is None:
                self.contract = self.web3.eth.contract(address=self.contract.address, abi=self.contract.abi)

            # Process the logs for the UTXOCreated event
            created_logs = self.contract.events.UTXOCreated().process_receipt(tx_receipt)

            # Process the logs for the UTXOSpent event
            spent_logs = self.contract.events.UTXOSpent().process_receipt(tx_receipt)

            # Check the logs for the UTXOCreated event
            if created_logs:
                utxo = created_logs[0]['args']['utxoId']

                # return utxo as hex
                utxo_id_hex = utxo.hex()
                print(f"UTXO Created, UTXO ID: {utxo_id_hex}")
                return 'UTXOCreated', utxo_id_hex

            # Check the logs for the UTXOSpent event
            elif spent_logs:
                utxo = spent_logs[0]['args']['utxoId']

                # return utxo as hex
                utxo_id_hex = utxo.hex()
                print(f"UTXOSpent, UTXO ID: {utxo_id_hex}")
                return 'UTXOSpent', utxo_id_hex

            else:
                raise Exception("No logs found")
