import sys
sys.path.append("..")

import unittest
from unittest.mock import patch, MagicMock
from ethereum.ethereum_wallet import EthereumWallet


class TestEthereumWallet(unittest.TestCase):
    @patch('ethereum.ethereum_wallet.Web3')
    def setUp(self, MockWeb3):
        # Mock the Web3 instance
        self.mock_web3_instance = MockWeb3.return_value
        self.mock_web3_instance.is_connected.return_value = True
        self.mock_web3_instance.provider = "mock_provider"

        # Use a test private key (replace with a valid test key)
        self.pkey = "0x4c0883a69102937d6231471b5dbb6204fe512961708279e5e6b8b7e6f3b7b7a9"

        # Initialize the EthereumWallet instance
        self.wallet = EthereumWallet(self.mock_web3_instance, self.pkey)

    def test_wallet_initialization(self):
        # Test if the wallet is initialized correctly
        self.assertIsNotNone(self.wallet.account)
        self.assertIsNotNone(self.wallet.w3)
        self.assertTrue(self.wallet.w3.is_connected())

    @patch('ethereum.ethereum_wallet.Web3')
    def test_wallet_balance(self, MockWeb3):
        # Mock the Web3 instance
        mock_web3_instance = MockWeb3.return_value
        mock_eth = MagicMock()
        mock_eth.get_balance.return_value = 1000000000000000000  # 1 Ether in Wei
        mock_web3_instance.eth = mock_eth

        # Initialize the EthereumWallet instance with the mocked Web3 instance
        self.wallet = EthereumWallet(mock_web3_instance, self.pkey)

        # Test if the wallet can retrieve the balance (in Wei)
        balance = self.wallet.get_balance()
        self.assertIsInstance(balance, int)
        self.assertEqual(balance, 1000000000000000000)

    @patch('ethereum.ethereum_wallet.Web3')
    def test_check_balance_zero(self, MockWeb3):
        # Mock the Web3 instance
        mock_web3_instance = MockWeb3.return_value
        mock_web3_instance.eth.get_balance.return_value = 0  # 0 Ether in Wei

        # Initialize the EthereumWallet instance with the mocked Web3 instance
        self.wallet = EthereumWallet(mock_web3_instance, self.pkey)

        # Mock the account address
        self.wallet.account = MagicMock()
        self.wallet.account.address = "0xYourAddress"

        # Test if the wallet can retrieve the balance (in Wei)
        balance = self.wallet.get_balance()
        self.assertEqual(balance, 0)

    @patch('ethereum.ethereum_wallet.Web3')
    def test_get_balance_large(self, MockWeb3):
        # Mock the Web3 instance
        mock_web3_instance = MockWeb3.return_value
        mock_web3_instance.eth.get_balance.return_value = 1000000000000000000000

        # Initialize the EthereumWallet instance with the mocked Web3 instance
        self.wallet = EthereumWallet(mock_web3_instance, self.pkey)

        # Mock the account address
        self.wallet.account = MagicMock()
        self.wallet.account.address = "0xYourAddress"

        # Test if the wallet can retrieve the balance (in Wei)
        balance = self.wallet.get_balance()
        self.assertEqual(balance, 1000000000000000000000)

    @patch('ethereum.ethereum_wallet.Web3')
    def test_get_balance_connection_issue(self, MockWeb3):
        # Mock the Web3 instance to simulate a disconnected state
        mock_web3_instance = MockWeb3.return_value
        mock_web3_instance.is_connected.side_effect = [True, False]  # Connected during init, disconnected during get_balance

        # Initialize the EthereumWallet instance with the mocked Web3 instance
        self.wallet = EthereumWallet(mock_web3_instance, self.pkey)

        # Test if the wallet raises a ConnectionError when trying to get the balance
        with self.assertRaises(ConnectionError) as context:
            self.wallet.get_balance()

        # Assert the exception message
        self.assertTrue("Web3 provider is not connected" in str(context.exception))

    @patch('ethereum.ethereum_wallet.EthereumWallet.get_balance')
    def test_get_balance_eth(self, mock_get_balance_wei):
        # Mock the get_balance_wei method to return a specific value in Wei
        mock_get_balance_wei.return_value = 1000000000000000000  # 1 ETH in Wei

        # Test if the wallet can retrieve the balance (in ETH)
        balance_eth = self.wallet.get_balance_eth()
        self.assertEqual(balance_eth, 1.0)


if __name__ == '__main__':
    unittest.main()
