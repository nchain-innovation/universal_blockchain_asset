import unittest
from unittest import mock

"""from web3_py.erc20 import ERC20
from web3_py.raw_transaction import RawTransaction
"""

from ethereum.ethereum_wallet import EthereumWallet
from web3 import Account

import sys
sys.path.append("..")


class TestEthereumWallet(unittest.TestCase):
    def setUp(self):
        self.config = {
            'ethereum_service': {
                "ethNodeUrl": "https://sepolia.infura.io/v3/",
                "apiKey": "25810eab24f5460ca96527cffa737d4f",
                "gas": "2000000",
                "gasPrice": "50",
                "maxGasPrice": "200"
            }
        }
        self.eth_priv_key = 'cfb2fb15d4976800871b0162ac6e95647070105ddbbae6e17622b4a93ad9f620'
        self.wallet = EthereumWallet()

    @mock.patch('web3.Web3.is_connected', return_value=True)
    def test_set_config(self, mock_is_connected):
        self.wallet.set_config(self.config)
        self.assertEqual(self.wallet.ethNodeUrl, self.config['ethereum_service']['ethNodeUrl'])
        self.assertEqual(self.wallet.apiKey, self.config['ethereum_service']['apiKey'])
        self.assertEqual(self.wallet.gas, self.config['ethereum_service']['gas'])
        self.assertEqual(self.wallet.gasPrice, self.config['ethereum_service']['gasPrice'])
        self.assertEqual(self.wallet.maxGasPrice, self.config['ethereum_service']['maxGasPrice'])
        self.assertTrue(self.wallet.web3.is_connected())

    def test_set_account(self):
        self.wallet.set_account(self.eth_priv_key)
        self.assertEqual(self.wallet.account.address, Account.from_key(self.eth_priv_key).address)


if __name__ == '__main__':
    unittest.main()
