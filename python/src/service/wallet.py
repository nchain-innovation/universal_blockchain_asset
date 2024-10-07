from tx_engine import Tx, Script
from tx_engine import Wallet as cg_wallet

from config import ConfigType

"""
BSV faucet for topping up wallets - https://witnessonchain.com/faucet/tbsv
"""


def address_to_locking_script(address: str) -> Script:
    # Given an address return the associated locking script
    return Script.parse(address_to_locking_script(address))


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

    def sign_tx_with_input(self, index: int, input_tx: Tx, tx: Tx) -> Tx:
        return self.wallet.sign_tx(index, input_tx, tx)

    def get_locking_script(self) -> Script:
        return self.wallet.get_locking_script()

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
