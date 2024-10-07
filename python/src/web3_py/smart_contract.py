import logging
from typing import Callable
from web3 import Web3
from web3.types import TxParams, Wei
from ethereum.ethereum_wallet import EthereumWallet
from web3.exceptions import ContractLogicError, TransactionNotFound, TimeExhausted
from web3.gas_strategies.time_based import medium_gas_price_strategy, fast_gas_price_strategy, slow_gas_price_strategy


from config import ConfigType
import json
import warnings

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartContract:

    # ------------------- Constructor --------------------
    def __init__(self, interface_config: ConfigType, w3: Web3):
        ''' Constructor for the SmartContract class
        '''
        assert interface_config['name'] == 'SmartContract'
        self.w3 = w3

        # Ensure config file has all required fields
        required_fields = ['abi_filename',
                           'bytecode_filename',
                           'contract_pkey',
                           'contract_deployment',
                           'gas_strategy',
                           'deploy_new_contract']

        if not all(field in interface_config for field in required_fields):
            missing_fields = [field for field in required_fields if field not in interface_config]
            raise ValueError(f"Missing required fields in configuration: {', '.join(missing_fields)}")

        # Load the ABI and Bytecode
        abi_filename = interface_config['abi_filename']
        bytecode_filename = interface_config['bytecode_filename']
        self.abi = self._load_abi(abi_filename)
        self.bytecode = self._load_bytecode(bytecode_filename)

        # Get the gas strategy, can be one of 'fast', 'medium', 'slow'
        gas_strategy = interface_config['gas_strategy']
        if gas_strategy == 'fast':
            self.gas_strategy = fast_gas_price_strategy
        elif gas_strategy == 'medium':
            self.gas_strategy = medium_gas_price_strategy
        elif gas_strategy == 'slow':
            self.gas_strategy = slow_gas_price_strategy
        else:
            raise ValueError(f"Invalid gas strategy: {gas_strategy}")

        # set the gas price strategy
        self.w3.eth.set_gas_price_strategy(self.gas_strategy)

        # Either: load existing contract OR create new contract
        deploy_new_contract = interface_config['deploy_new_contract']

        if deploy_new_contract:
            contract_pkey = interface_config['contract_pkey']

            if not contract_pkey:
                logger.error("Contract private key is required to deploy a new contract")
                raise ValueError("Contract owner private key (contract_pkey) not found in config")

            contract_wallet = EthereumWallet(w3, contract_pkey)
            self._deploy_contract(contract_wallet)

        else:
            self.contract_deployment = interface_config['contract_deployment']

            if not self.contract_deployment:
                logger.error("Contract deployment address is required to load an existing contract")
                raise ValueError("Contract deployment address (contract_deployment) not found in config")

            self._load_contract(self.contract_deployment)

        assert self.contract is not None
        assert self.contract_deployment is not None

    # ------------------- Private methods --------------------
    # --------------------------------------------------------
    def _load_abi(self, filename: str) -> dict:
        logger.info(f"Loading ABI from: {filename}")
        try:
            with open(filename) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File {filename} not found.")
            raise FileNotFoundError(f"File {filename} not found.")

    # --------------------------------------------------------
    def _load_bytecode(self, filename: str) -> str:
        logger.info(f"Loading Bytecode from: {filename}")
        try:
            with open(filename) as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"File {filename} not found.")
            raise FileNotFoundError(f"File {filename} not found.")

    # --------------------------------------------------------
    def _deploy_contract(self, wallet: EthereumWallet):
        logger.info("Deploying contract")

        # Check if connected to the network
        if self.w3.is_connected():
            logger.info("Connected to Sepolia network")
        else:
            logger.error("Connection failed")
            raise ConnectionError("Failed to connect to Sepolia network")

        # set the gas price
        gas_price: Wei = self.get_gas_price()

        # Estimate the gas required to deploy the contract
        contract = self.w3.eth.contract(abi=self.abi, bytecode=self.bytecode)
        gas_estimate = contract.constructor().estimate_gas()
        gas_cost = gas_estimate + 5000  # Add a buffer of 5000 gas units

        # Calculate the total gas cost in Wei
        total_gas_cost = gas_cost * gas_price

        # Get current balance of the contract account
        balance = wallet.get_balance()
        logger.info(f"Contract Account Balance: {balance}, Gas estimate: {total_gas_cost}")

        # Check if the Contract account has enough balance to cover the gas cost
        if balance < total_gas_cost:
            logger.error("Insufficient balance! Transaction will fail due to lack of funds to cover gas.")
            raise Exception("Insufficient balance to deploy contract")
        else:
            logger.info("Sufficient balance. Proceeding with contract deploymnet.")

            # Get the nonce
            nonce = self.w3.eth.get_transaction_count(wallet.account.address)

            # Build a transaction
            transaction: TxParams = {
                'nonce': nonce,
                'gas': gas_cost,
                'gasPrice': gas_price,
                'from': wallet.account.address,
            }

            logger.info(f"Transaction details: {transaction}")

            # Get the contract deployment
            contract_txn = contract.constructor().build_transaction(transaction)

            # Sign the transaction
            signed_txn = wallet.sign_transaction(contract_txn)

            # Send the transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logger.info(f"Transaction hash: {tx_hash.hex()}")

            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            if tx_receipt['status'] == 1:
                logger.info(f"Transaction succeeded. Block number: {tx_receipt['blockNumber']}")
            else:
                logger.error(f"Transaction failed. Block number: {tx_receipt['blockNumber']}")
                raise Exception("Transaction failed")

            self.contract_deployment = tx_receipt['contractAddress']
            logger.info(f"Contract deployed at address: {self.contract_deployment}")

            # Create and store the contract instance
            self.contract = self.w3.eth.contract(address=self.contract_deployment, abi=self.abi)

    # --------------------------------------------------------
    def _load_contract(self, contract_deployment):
        logger.info(f"Loading contract from: {contract_deployment} ")
        self.contract = self.w3.eth.contract(address=contract_deployment, abi=self.abi)

    # --------------------------------------------------------
    def _txhash_to_utxoid(self, tx_hash):
        logger.info(f"Converting tx_hash to UTXO ID, tx_hash: {tx_hash}")

        # Get the transaction receipt
        tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)

        # Parse the logs
        logs = self.contract.events.UTXOCreated().process_receipt(tx_receipt)

        # Get the TXID from the logs
        if logs:
            utxo = logs[0]['args']['utxoId']
            utxo_id_hex = utxo.hex()
            logger.info(f"UTXO ID: {utxo_id_hex}")

        else:
            logger.error("No logs found")
            raise Exception("No logs found")

        return utxo

    # --------------------------------------------------------
    def _build_create_ownership_transaction(self, transaction: TxParams) -> TxParams:
        logger.info("Building create ownership transaction")
        return self.contract.functions.createUTXO().build_transaction(transaction)

    # --------------------------------------------------------
    def _build_spend_ownership_transaction(self, transaction: TxParams, utxo: str, cpid: str) -> TxParams:
        logger.info(f"Building spend ownership transaction, UTXO: {utxo}, CPID: {cpid}")
        return self.contract.functions.spendUTXO(utxo, cpid).build_transaction(transaction)

    # --------------------------------------------------------
    def _send_transaction(self, wallet: EthereumWallet, gas_price: Wei, gas_limit: int, build_transaction: Callable[[TxParams], TxParams], retries: int = 3) -> str:
        try:
            # Get the nonce
            nonce = self.w3.eth.get_transaction_count(wallet.account.address)

            # Build a transaction
            transaction: TxParams = {
                'nonce': nonce,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'from': wallet.account.address,
            }

            logger.info(f"Transaction details: {transaction}")

            # Build the transaction
            create_txn = build_transaction(transaction)

            # Sign the transaction
            signed_txn = wallet.sign_transaction(create_txn)

            # Send the signed transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            logger.info(f"Transaction hash: {tx_hash.hex()}")

            try:
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                if tx_receipt['status'] == 1:
                    logger.info(f"Transaction succeeded. Block number: {tx_receipt['blockNumber']}")
                    return tx_hash.hex()
                else:
                    logger.error(f"Transaction failed. tx_receipt: {tx_receipt}")
                    raise Exception("Transaction failed")

            except (TimeExhausted, TransactionNotFound) as e:
                logger.error(f"TimeExhausted not found or timed out: {e}")
                if retries > 0:
                    logger.info(f"Retrying transaction with higher gas price. Retries left: {retries}")
                    return self._send_transaction(wallet, Wei(int(gas_price * 1.2)), gas_limit, build_transaction, retries - 1)
                else:
                    raise

        except Exception as e:
            logger.error(f"Outer Error: {e}")
            raise

    # ------------------- Public methods --------------------
    # --------------------------------------------------------
    def refresh_web3(self, w3: Web3):
        self.w3 = w3

    # --------------------------------------------------------
    def get_gas_price(self) -> Wei:
        ''' Get the gas price in Wei - 20 gwei considered a reasonable default value
        under normal network conditions
        '''
        logger.info("Getting gas price")
        gas_price = self.w3.eth.generate_gas_price()

        if gas_price is None:
            gas_price = self.w3.to_wei('20', 'gwei')  # Provide a default value of 20 gwei
        else:
            gas_price = Wei(int(gas_price * 1.2))  # Increase the gas price by 20% because it's never enough!

        return gas_price

    # --------------------------------------------------------
    def create_ownership(self, wallet: EthereumWallet) -> str:
        logger.info("Creating ownership")

        gas_cost: int = 53000  # from trial and error - works better than estimate_gas()

        # Check if connected to the network
        if self.w3.is_connected():
            logger.info("Connected to Sepolia network")
        else:
            logger.error("Connection failed")
            raise ConnectionError("Failed to connect to Sepolia network")

        try:
            # set the gas price
            gas_price = self.get_gas_price()
            logger.info(f"Gas price: {gas_price}")

            # Calculate the total gas cost in Wei
            total_gas_cost = gas_cost * gas_price

            # Get current balance of the Eth account
            balance = wallet.get_balance()
            logger.info(f"Account Balance (Wei): {balance}, Gas estimate: {total_gas_cost}")

            # Check if the funds will cover the transaction
            if balance < total_gas_cost:
                logger.error("Insufficient balance! Transaction will fail due to lack of funds to cover gas.")
                raise Exception("Insufficient balance to call createUTXO")

            else:
                logger.info("Sufficient balance. Proceeding with createUTXO.")
                return self._send_transaction(wallet, gas_price, gas_cost, self._build_create_ownership_transaction)

        except ContractLogicError as e:
            logger.error(f"Contract logic error: {e}")
            raise

        except Exception as e:
            logger.error(f"Create Ownership Error: {e}")
            raise

    # --------------------------------------------------------
    def spend_ownership(self, tx_hash: str, cpid: str, wallet: EthereumWallet):
        logger.info(f"Spending ownership, tx_hash: {tx_hash}, CPID: {cpid}")

        # Check if connected to the network
        if self.w3.is_connected():
            logger.info("Connected to Sepolia network")
        else:
            logger.error("Connection failed")
            raise ConnectionError("Failed to connect to Sepolia network")

        utxo = None

        try:
            utxo = self._txhash_to_utxoid(tx_hash)
        except Exception as e:
            print(e)
            raise Exception(f"Error converting tx_hash to UTXO ID, tx_hash: {tx_hash}, error: {e}")

        if utxo is None:
            raise Exception("UTXO ID not found")

        try:

            # set the gas price
            gas_price = self.get_gas_price()
            logger.info(f"Gas price: {gas_price}")

            # Estimate the gas required to call spendUTXO - this also exercises the contract logic
            gas_estimate = self.contract.functions.spendUTXO(utxo, cpid).estimate_gas({
                'from': wallet.account.address,
            })
            gas_cost = gas_estimate + 5000      # Add a buffer of 5000 gas units

            # Calculate the total gas cost in Wei
            total_gas_cost = gas_cost * gas_price

            # Get current balance of the Eth account
            balance = wallet.get_balance()
            logger.info(f"Account Balance (Wei): {balance}, Gas estimate: {total_gas_cost}")

            # Check if the funds will cover the transaction
            if balance < total_gas_cost:
                logger.error("Insufficient balance! Transaction will fail due to lack of funds to cover gas.")
                raise Exception("Insufficient balance to call spendUTXO")

            else:
                logger.info("Sufficient balance. Proceeding with spendUTXO.")

                return self._send_transaction(
                    wallet,
                    gas_price,
                    gas_cost,
                    lambda tx: self._build_spend_ownership_transaction(tx, utxo, cpid)
                )

        except ContractLogicError as e:
            logger.error(f"Contract logic error: {e}")
            raise

        except Exception as e:
            logger.error(f"Spend Ownership Error: {e}")
            raise

    # --------------------------------------------------------
    def tx_spent_status(self, tx_hash):
        logger.info(f"Checking if tx is spent, tx_hash: {tx_hash}")
        utxo = None
        try:
            utxo = self._txhash_to_utxoid(tx_hash)
        except Exception as e:
            raise Exception(f"Error converting tx_hash to UTXO ID, tx_hash: {tx_hash}, error: {e}")

        if utxo is None:
            raise Exception("UTXO ID not found")

        # Call isUTXOSpent
        return self.contract.functions.isUTXOSpent(utxo).call()

    # --------------------------------------------------------
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

    # --------------------------------------------------------
    def get_event_and_utxo(self, tx_hash):
        print(f"Getting event and UTXO for tx_hash: {tx_hash}")

        # Suppress the UserWarning
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=UserWarning)

            # Get the transaction receipt
            tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)

            # Get the contract instance
            logger.info(f"Contract: {self.contract}")

            # Process the logs for the UTXOCreated event
            created_logs = self.contract.events.UTXOCreated().process_receipt(tx_receipt)

            # Process the logs for the UTXOSpent event
            spent_logs = self.contract.events.UTXOSpent().process_receipt(tx_receipt)

            # Check the logs for the UTXOCreated event
            if created_logs:
                utxo = created_logs[0]['args']['utxoId']

                # return utxo as hex
                utxo_id_hex = utxo.hex()
                logger.info(f"UTXO Created, UTXO ID: {utxo_id_hex}")
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
