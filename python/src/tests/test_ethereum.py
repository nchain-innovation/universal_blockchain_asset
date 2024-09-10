import unittest
from unittest import mock

"""from web3_py.erc20 import ERC20
from web3_py.raw_transaction import RawTransaction
"""
from web3_py.smart_contract import SmartContract
from ethereum.ethereum_wallet import EthereumWallet
# import sys
# sys.path.append("..")

import sys
sys.path.append("..")


class TestEthereumInterfaceFactory(unittest.TestCase):
    def setUp(self):

        self.config = {
            'ethereum_service': {
                "ethNodeUrl": "https://sepolia.infura.io/v3/",
                "apiKey": "25810eab24f5460ca96527cffa737d4f",
                "gas": 2000000,
                "gasPrice": 50,
                "maxGasPrice": 200,
                "interface_type": "SmartContract"
            },
            'eth_priv_key': 'cfb2fb15d4976800871b0162ac6e95647070105ddbbae6e17622b4a93ad9f620',
            'interface': [
                {
                    'name': 'SmartContract',
                    'contract_pkey': "",
                    'contract_deployment': '0xf120D32bb10A2aE2971f9Aa026aBE8F0dA9709fb',
                    'abi_filename': 'bytecode.txt',
                    'bytecode_filename': 'bytecode.txt'
                }
            ]
        }

        # Mock the contents of the .abi and .bytecose files
        self.abi_content = '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"type":"function"}]'
        self.bytecode_content = '608060405234801562000010575f80fd5b50604051'

        # Mock the open function to return the mock file content
        self.open_mock = mock.mock_open(read_data=self.abi_content)
        self.open_patch = mock.patch('builtins.open', self.open_mock)
        self.open_patch.start()

        self.eth_wallet = EthereumWallet()
        self.eth_wallet.set_config(self.config)
        self.eth_wallet.set_account(self.config["eth_priv_key"])

    def test_ethereum_interface_factory(self):
        smart_contract: SmartContract = SmartContract(self.config, self.eth_wallet.web3)
        self.assertIsInstance(smart_contract, SmartContract)

        """
        erc20 = ethereum_interface_factory('ERC20', self.config['ethNodeUrl'], self.config['apiKey'], self.config['privateKey'], self.config['gas'], self.config['gasPrice'], erc20_config)
        self.assertIsInstance(erc20, ERC20)
        with self.assertRaises(ValueError):
        ethereum_interface_factory('InvalidType', self.config['ethNodeUrl'], self.config['apiKey'], self.config['privateKey'], self.config['gas'], self.config['gasPrice'], self.config)
        """
    def tearDown(self):
        # Stop patching open
        self.open_patch.stop()


if __name__ == '__main__':
    unittest.main()
