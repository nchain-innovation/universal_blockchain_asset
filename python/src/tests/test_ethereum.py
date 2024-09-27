import unittest
from unittest import mock
from eth_account.signers.local import LocalAccount
from ethereum.ethereum_wallet import EthereumWallet


class TestEthereumWallet(unittest.TestCase):
    def setUp(self):
        self.config = {
            'ethereum_service': {
                "ethNodeUrl": "https://sepolia.infura.io/v3/YOUR_INFURA_PROJECT_ID",
                "apiKey": "YOUR_API_KEY",
                "gas": "2000000",
                "gasPrice": "50",
                "maxGasPrice": "200"
            }
        }
        self.eth_priv_key = '8ac317c9ad1af866bdd18cf2b52733eaa34cd969269c78dcf2365c46b0399074'
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
        self.assertIsInstance(self.wallet.account, LocalAccount)


if __name__ == '__main__':
    unittest.main()
