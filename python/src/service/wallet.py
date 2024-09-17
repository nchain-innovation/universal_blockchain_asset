from typing import List

#from tx_engine.engine.keys import wif_to_key, PrivateKey
#from tx_engine.engine.standard_scripts import p2pkh_script
#from tx_engine.engine.script import Script
##from tx_engine.engine.helper import decode_base58

from tx_engine import Tx, Script, address_to_public_key_hash
from tx_engine import Wallet as cg_wallet
#from tx_engine.tx.tx_sign_with_inputs import sign_transaction_with_inputs

from config import ConfigType

"""
BSV faucet for topping up wallets - https://witnessonchain.com/faucet/tbsv
"""


def address_to_locking_script(address: str) -> Script:
    # Given an address return the associated locking script
    #return p2pkh_script(decode_base58(address))
    script: bytes = address_to_locking_script(address)
    return Script.parse(bytes)


class Wallet:
    """ This class represents the Wallet functionality
    """
    def __init__(self):
        self.blockchain_enabled: bool = False
        self.wallet: cg_wallet

    def set_config(self, config: ConfigType):
        """ Given the wallet configuration, set up the wallet"""
        # Keys and addresses
        wif_key = config["bitcoin_key"]
        self.wallet = cg_wallet(wif_key)

    def set_wif(self, wif_key: str):
        """ Given the wif_key, set up the wallet"""
        self.wallet = cg_wallet(wif_key)

    #def sign_tx_with_inputs(self, input_txs: List[Tx], tx: Tx) -> bool:
    #    return sign_transaction_with_inputs(input_txs, tx, self.private_key)

    def sign_tx_with_input(self, index: int, input_tx: Tx, tx: Tx) -> Tx:
        return self.wallet.sign_tx(index, input_tx, tx)
    
    def get_locking_script(self) -> Script:
        return self.wallet.get_locking_script()
        #return p2pkh_script(decode_base58(self.address))

    def get_locking_script_as_hex(self) -> str:
        return self.wallet.get_locking_script().raw_serialize().hex()

    def get_public_key_as_hexstr(self) -> str:
        return self.wallet.get_public_key_as_hexstr()


if __name__ == '__main__':
    from config import load_config
    import pprint
    pp = pprint.PrettyPrinter()

    CONFIG_FILE = "../../data/token-server.toml"
    config = load_config(CONFIG_FILE)
    issuer_wallet = cg_wallet()
    issuer_wallet.set_config(config["issuer_wallet"])

    pp.pprint(issuer_wallet.__dict__)
