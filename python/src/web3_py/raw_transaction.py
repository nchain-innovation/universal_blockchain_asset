from web3_py.ethereum_interface import EthereumInterface


class RawTransaction(EthereumInterface):
    def __init__(self, ethNodeUrl, apiKey, privateKey, gas, gasPrice, config):
        super().__init__(ethNodeUrl, apiKey, privateKey, gas, gasPrice)

        # Check if 'reuse_account' is in the config and set the reuse flag accordingly
        if 'reuse_account' in config:
            self.reuse = config['reuse_account']
        else:
            self.reuse = False
        print("RawTransaction constructor")

    # private function to get the nonce
    def _get_nonce(self):
        try:
            nonce = self.web3.eth.get_transaction_count(self.account.address)
            return nonce
        except Exception as e:
            print("Error in getting nonce: ", e)
            return None

    # If create is True, check the nonce is 0,
    # otherwise it's a spending transaction, check the nonce is 1
    # If resuse is True, use modulus 2 to check the nonce
    # (therefore can reuse the account for sequential tokens)
    # In summary:
    # 0 is not a UTXO
    # 1 is a UTXO
    def _check_nonce(self, nonce: int, create: bool):
        nonce = self._get_nonce()

        if nonce is None:
            raise Exception("Error in getting nonce")

        # if reusing the account, used the modulus of 2
        tmp_nonce = nonce
        if self.reuse:
            tmp_nonce = nonce % 2

        # Creating a new ownership, nonce should be 0
        if create:
            if tmp_nonce != 0:
                return False

        # Spending a transaction, it is a "UTXO" therefore nonce should be 1
        else:
            if tmp_nonce != 1:
                return False
        return True

    def create_ownership(self):
        nonce = self._get_nonce()
        if nonce is None:
            raise Exception("Error in getting nonce")

        if self._check_nonce(nonce, True) is False:
            if self.reuse:
                raise Exception(f"Nonce is {nonce}. Nonce % 2 should be 0 for creating ownership")
            else:
                raise Exception(f"Nonce is {nonce} (was expecting 0). Ownership already exists")

        # check if the account has sufficient funds for the transaction
        if self.check_funds(0, ) is False:
            raise Exception("Insufficient funds for the transaction")

        # create a raw transaction
        transaction = {
            'from': self.account.address,
            'to': self.account.address,
            'value': 0,  # Set the value to 0 for a self-transaction
            'gas': self.gas,
            'gasPrice': self.web3.to_wei(self.gasPrice, 'gwei'),
            'nonce': nonce,
            'data': '',  # Set the data field to an empty string
        }

        # sign the transaction
        # signed_txn = self.web3.eth.account.sign_transaction(transaction, self.privateKey)
        signed_txn = self.account.sign_transaction(transaction)

        # send the transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Transaction hash: {tx_hash.hex()}")
        return tx_hash.hex()

    def spend_ownership(self, txid: str, CPID: str):
        print("Spending ownership: TXID not used, <TODO>")

        nonce = self._get_nonce()
        if nonce is None:
            raise Exception("Error in getting nonce")
        if self._check_nonce(nonce, False) is False:
            if self.reuse:
                raise Exception(f"Nonce is {nonce}. Nonce % 2 should be 0 or 1 for spending the ownership")
            else:
                raise Exception(f"Nonce is {nonce}. It should be 1 for spending the ownership")

        # check if the account has sufficient funds for the transaction
        if self.check_funds(0) is False:
            raise Exception("Insufficient funds for the transaction")

        # create a raw transaction
        transaction = {
            'from': self.account.address,
            'to': self.account.address,
            'value': 0,  # Set the value to 0 for a self-transaction
            'gas': self.gas,
            'gasPrice': self.web3.to_wei(self.gasPrice, 'gwei'),
            'nonce': nonce,
            'data': CPID,  # Set the data field to the CPID
        }

        # sign the transaction
        # signed_txn = self.web3.eth.account.sign_transaction(transaction, self.privateKey)
        signed_txn = self.account.sign_transaction(transaction)

        # send the transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Transaction hash: {tx_hash.hex()}")
        return tx_hash.hex()

    # check the spent status by checking the nonce of the account
    # if the nonce is == 1 then it is "unspent"
    def tx_spent_status(self, tx_hash: str):
        # get the transaction receipt
        tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
        if tx_receipt is None:
            raise Exception("Transaction receipt not found")
        print(f"Transaction receipt: {tx_receipt}")

        # extract the "to" account from the transaction receipt
        to_account = tx_receipt['to']
        if to_account is None:
            raise Exception("To account not found in transaction receipt")

        # get the nonce of the "to" account
        nonce = self.web3.eth.get_transaction_count(to_account)
        print(f"Nonce of the 'to' account: {nonce}")

        return self._check_nonce(nonce, False)
