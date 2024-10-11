#!/usr/bin/python3
import unittest
from unittest.mock import patch, call, mock_open
import sys

sys.path.append("..")

from service.commitment_service import CommitmentService, FinancingService, \
    CommitmentPacket, EthereumService, \
    CommitmentStore, Tx
from service.token_description import token_store, TokenStore, token_descriptor
from tx_engine import MockInterface

COMMITMENT_STORE_FILE = './fakepath/test-commitments.json'
TOKEN_FILE_STORE = './fakepath/token_store.json'

CONFIG = {
    'actor': [
        {'name': 'Alice',
            'token_key': 'alice_token_key_placeholder',
            'token_key_curve': 'NIST256p',
            'bitcoin_key': 'alice_bitcoin_key_placeholder',
            'eth_key': 'alice_eth_key_placeholder'},
        {'name': 'Bob',
            'token_key': 'bob_token_key_placeholder',
            'token_key_curve': 'NIST256p',
            'bitcoin_key': 'bob_bitcoin_key_placeholder',
            'eth_key': 'bob_eth_key_placeholder'},
        {'name': 'Ted',
            'token_key': 'ted_token_key_placeholder',
            'token_key_curve': 'NIST256p',
            'bitcoin_key': 'ted_bitcoin_key_placeholder',
            'eth_key': 'ted_eth_key_placeholder'},
    ],
    'commitment_service': {
        'networks': ['BSV', 'ETH']
    },
    'ethereum_service': {
        'ethNodeUrl': 'https://sepolia.infura.io/v3/',
        'apiKey': 'your_api_key_placeholder',
        'interface_type': "SmartContract"
    },
    'interface': [
        {
            'name': 'SmartContract',
            'deploy_new_contract': False,
            'contract_pkey': 'your_contract_pkey_placeholder',
            'contract_deployment': 'your_contract_deployment_placeholder',
            'abi_filename': '../web3_py/build/SmartUTXO.abi',
            'bytecode_filename': '../web3_py/build/SmartUTXO.bytecode',
            'gas_strategy': 'fast'
        }
    ],
    'commitment_store': {
        'filepath': COMMITMENT_STORE_FILE
    },
    'token_info': {
        'token_file_store': TOKEN_FILE_STORE
    },
    'token': [
        {'ipfs_cid': 'asset_data', 'description': 'asset description'
         }],
    'finance_service': {
        'url': 'http://financing_service:8070',
        'client_id': 'uba',
    },
    'blockchain': {
        'network_type': 'testnet',
        'interface_type': 'mock'
    }
}


class TestCommitmentService(unittest.TestCase):

    @patch('service.commitment_service.CommitmentStore.load', return_value=None)
    @patch('service.commitment_service.CommitmentStore.set_config')
    @patch('service.commitment_service.Wallet.set_wif', return_value=None)
    @patch('service.commitment_service.TokenWallet.set_key', return_value=None)
    @patch('service.commitment_service.EthereumWallet', autospec=True)
    @patch('service.commitment_service.FinancingService')
    @patch('service.commitment_service.EthereumService')
    def setUp(self,
              MockEthereumService,
              mock_financing_service,
              mock_ethereum_wallet,
              mock_set_key,
              mock_set_wif,
              mock_set_config,
              mock_load,
              ):
        # Store the mock objects as instance attributes
        self.mock_set_wif = mock_set_wif
        self.mock_set_key = mock_set_key
        # self.mock_token_wallet = mock_token_wallet
        self.mock_ethereum_wallet = mock_ethereum_wallet
        self.mock_load = mock_load
        self.mock_set_config = mock_set_config

        # Configure the mock financing service to return example data
        self.mock_financing_service = mock_financing_service
        self.mock_financing_service.get_funds.return_value = {
            'status': 'Success',
            'outpoints': [{'hash': 'c09e7e87c5d18c93e8e74e7c3baf34799ecf3e720b2b7b473edae4d009a9e322', 'index': 1}],
            'tx': '0100000001213fddedbbb93a5a678b69f2f884a35f655eed0c10acca29e7d6ad28206944e5000000006a47304402207b487b7dd7a87f2ae5968020f7ecc26b47d959481ee22f7c490acf64be263a6b02200c8ab50684fce2e3a3627cc84b6d502f9538b1d4bc5ba827f7e4dea2522c5dc74121024f8d67f0a5ec11e72cc0f2fa5c272b69fd448b933f92a912210f5a35a8eb2d6affffffff026cd18500000000001976a914661657ba0a6b276bb5cb313257af5cc416450c0888ac64000000000000001976a9147d981c463355c618e9666044315ef1ffc523e87088ac00000000'
        }

        # Use the mock object in place of the real service
        results = mock_financing_service.get_funds(1000, 'mock_locking_script')

        # Check that the method was called with the expected arguments
        mock_financing_service.get_funds.assert_called_with(1000, 'mock_locking_script')

        # Check the return value
        assert isinstance(results, dict), f"Expected dict, got {type(results)}"

        self.mock_ethereum_service_instance = MockEthereumService.return_value

        # Mock the EthereumWallet instance
        self.mock_ethereum_wallet_instance = mock_ethereum_wallet.return_value

        # Create an instance of CommitmentService
        self.service = CommitmentService()

        # Set config using the provided CONFIG
        self.service.set_config(CONFIG)

        # self.service.actors_token_wallets: Dict[str, mock_token_wallet] = {}

    def test_initialization(self):
        # Create an instance of CommitmentService
        service = CommitmentService()

        # Check if the finance_service attribute is an instance of FinancingService
        self.assertIsInstance(service.finance_service, FinancingService)

        # Check if the actors_wallets attribute is an empty dictionary
        self.assertEqual(service.actors_wallets, {})

        # Check if the actors_token_wallets attribute is an empty dictionary
        self.assertEqual(service.actors_token_wallets, {})

        # Check if the actors_eth_wallets attribute is an empty dictionary
        self.assertEqual(service.actors_eth_wallets, {})

        # Check if the networks attribute is an empty list
        self.assertEqual(service.networks, [])

        # Check if the commitment_store attribute is an instance of CommitmentStore
        self.assertIsInstance(service.commitment_store, CommitmentStore)

        # Check if the ethereum_service attribute is an instance of EthereumService
        self.assertIsInstance(service.ethereum_service, EthereumService)

    @patch('service.commitment_service.Wallet.set_wif', return_value=None)
    @patch('service.commitment_service.TokenWallet.set_key', return_value=None)
    @patch('service.commitment_service.CommitmentService.set_actors', return_value=None)
    @patch('service.commitment_service.FinancingService')
    @patch('service.commitment_service.CommitmentStore')
    @patch('service.commitment_service.EthereumService')
    def test_set_config(self, MockEthereumService, MockCommitmentStore, mock_financing_service, mock_set_actors, mock_set_key, mock_set_wif):
        # Mock the methods that will be called within set_config
        mock_financing_service_instance = mock_financing_service.return_value
        mock_commitment_store_instance = MockCommitmentStore.return_value
        mock_ethereum_service_instance = MockEthereumService.return_value

        # Create an instance of CommitmentService
        service = CommitmentService()

        # Set config using the provided CONFIG
        service.set_config(CONFIG)

        # # Check if the finance_service's set_config method was called
        mock_financing_service_instance.set_config.assert_called_with(CONFIG)

        # check if service.blockchain_interface is set to MockInterface
        self.assertIsInstance(service.blockchain_interface, MockInterface)

        # # Check if the ethereum_service's set_config method was called
        mock_ethereum_service_instance.set_config.assert_called_with(CONFIG)

        # # Check if the networks attribute is set correctly
        self.assertEqual(service.networks, CONFIG["commitment_service"]["networks"])  # type: ignore

        # # Check if the commitment_store's set_config and load methods were called
        mock_commitment_store_instance.set_config.assert_called_with(CONFIG)
        mock_commitment_store_instance.load.assert_called()

        # Check if service.token_store is an instance of TokenStore
        self.assertIsInstance(token_store, TokenStore)

        # The expected token structure
        expected_tokens = {
            'asset_data': token_descriptor(ipfs_cid='asset_data', description='asset description', cpid='')
        }

        # Check if the tokens in token_store match the expected tokens
        self.assertEqual(token_store.tokens, expected_tokens)

    def test_set_actors(self):
        # Check if the actors_wallets, actors_token_wallets, and actors_eth_wallets are populated correctly
        self.assertIn('Alice', self.service.actors_wallets)
        self.assertIn('Bob', self.service.actors_wallets)
        self.assertIn('Ted', self.service.actors_wallets)

        self.assertIn('Alice', self.service.actors_token_wallets)
        self.assertIn('Bob', self.service.actors_token_wallets)
        self.assertIn('Ted', self.service.actors_token_wallets)

        self.assertIn('Alice', self.service.actors_eth_wallets)
        self.assertIn('Bob', self.service.actors_eth_wallets)
        self.assertIn('Ted', self.service.actors_eth_wallets)

        # Check if the Wallet's set_wif method was called for each actor
        expected_calls = [
            call(CONFIG['actor'][0]['bitcoin_key']),   # type: ignore
            call(CONFIG['actor'][1]['bitcoin_key']),   # type: ignore
            call(CONFIG['actor'][2]['bitcoin_key'])    # type: ignore
        ]
        self.mock_set_wif.assert_has_calls(expected_calls, any_order=True)

        # Check if the TokenWallet's set_key method was called for each actor
        expected_calls = [
            call(CONFIG['actor'][0]['token_key'], CONFIG['actor'][0]['token_key_curve']),   # type: ignore
            call(CONFIG['actor'][1]['token_key'], CONFIG['actor'][1]['token_key_curve']),   # type: ignore
            call(CONFIG['actor'][2]['token_key'], CONFIG['actor'][2]['token_key_curve'])    # type: ignore
        ]
        self.mock_set_key.assert_has_calls(expected_calls, any_order=True)

        # Check if the EthereumWallet's constructor was called for each actor
        expected_calls = [
            call(self.mock_ethereum_service_instance.web3, CONFIG['actor'][0]['eth_key']),   # type: ignore
            call(self.mock_ethereum_service_instance.web3, CONFIG['actor'][1]['eth_key']),   # type: ignore
            call(self.mock_ethereum_service_instance.web3, CONFIG['actor'][2]['eth_key'])    # type: ignore
        ]
        self.mock_ethereum_wallet.assert_has_calls(expected_calls, any_order=True)

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("os.path.exists", return_value=True)
    @patch('service.commitment_service.Wallet.get_locking_script_as_hex', return_value='mock_locking_script')
    @patch('service.commitment_service.TokenWallet.get_signature_scheme', return_value='NIST256p')
    @patch('service.commitment_service.TokenWallet.get_token_public_key', return_value='mock_token_public_key')
    @patch('service.commitment_service.TokenWallet.sign_commitment_packet_digest', return_value=b'0x123456')
    @patch('service.commitment_service.verify_signature', return_value=True)
    def test_issuance(self, ver_sig, mock_sig, mock_pub_key, mock_sig_scheme, mock_get_locking_script, mock_exists, mock_open):
        """ Test the creation of an issuance commitment packet
        """
        self.service.finance_service = self.mock_financing_service

        result = self.service.create_issuance_commitment("Alice", "asset_id", "asset_data", "BSV")

        self.assertIsNotNone(result)
        assert result is not None
        (cpid, cp) = result
        self.assertTrue(isinstance(cpid, str))
        self.assertTrue(isinstance(cp, CommitmentPacket))
        self.assertEqual(cp.asset_id, 'asset_id')
        self.assertEqual(cp.data, 'asset_data')
        self.assertEqual(cp.blockchain_id, 'BSV')
        self.assertIsNone(cp.previous_packet)

        # Check Commitment state
        # Can Bob transfer (yes)
        self.assertTrue(self.service.can_transfer(cpid, "Bob", is_owner=False))
        self.assertTrue(self.service.can_transfer(cpid, "Ted", is_owner=False))
        # Can Alice transfer (no)
        self.assertFalse(self.service.can_transfer(cpid, "Alice", is_owner=False))

        # Can Alice complete the transfer? (no)
        self.assertFalse(self.service.can_complete_transfer(cpid, "Alice"))
        self.assertFalse(self.service.can_complete_transfer(cpid, "Bob"))

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("os.path.exists", return_value=True)
    @patch('service.commitment_service.Wallet.get_locking_script_as_hex', return_value='mock_locking_script')
    @patch('service.commitment_service.TokenWallet.get_signature_scheme', return_value='NIST256p')
    @patch('service.commitment_service.TokenWallet.get_token_public_key', return_value='mock_token_public_key')
    @patch('service.commitment_service.TokenWallet.sign_commitment_packet_digest', return_value=b'0x123456')
    @patch('service.commitment_service.verify_signature', return_value=True)
    def test_issuance_and_template(self, ver_sig, mock_sig, mock_pub_key, mock_sig_scheme, mock_get_locking_script, mock_exists, mock_open):
        """ Test the creation of an issuance commitment packet
            followed by the creation of a commitment packet for transfer
        """
        # Configure the mock to return different public keys for each call
        mock_pub_key.side_effect = ['mock_public_key_1', 'mock_public_key_2']

        self.service.finance_service = self.mock_financing_service

        result = self.service.create_issuance_commitment("Alice", "asset_id", "asset_data", "BSV")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid, cp) = result
        self.assertTrue(isinstance(cpid, str))
        self.assertTrue(isinstance(cp, CommitmentPacket))
        self.assertEqual(cp.asset_id, 'asset_id')
        self.assertEqual(cp.data, 'asset_data')
        self.assertEqual(cp.blockchain_id, 'BSV')
        self.assertIsNone(cp.previous_packet)

        result = self.service.create_transfer_template(cpid, "Bob", "BSV")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid2, cp2) = result
        self.assertTrue(isinstance(cpid2, str))
        self.assertTrue(isinstance(cp2, CommitmentPacket))
        # Check ids differ
        self.assertNotEqual(cpid, cpid2)
        # Check expected data matches
        self.assertEqual(cp2.asset_id, 'asset_id')
        self.assertEqual(cp2.data, 'asset_data')
        self.assertEqual(cp2.blockchain_id, 'BSV')
        # Check linked to previous_packet
        self.assertEqual(cp2.previous_packet, cpid)
        # Check signature is not completed
        self.assertIsNone(cp2.signature)
        # Check public_key signature is completed
        self.assertNotEqual(cp2.public_key, cp.public_key)

        # Check Commitment state
        # Can Alice complete the transfer? (yes)
        self.assertTrue(self.service.can_complete_transfer(cpid2, "Alice"))
        # Can Bob complete the transfer? (no)
        self.assertFalse(self.service.can_complete_transfer(cpid2, "Bob"))
        self.assertFalse(self.service.can_complete_transfer(cpid2, "Ted"))
        self.assertFalse(self.service.can_complete_transfer(cpid2, "Fred"))

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("os.path.exists", return_value=True)
    @patch('service.commitment_service.Wallet.get_locking_script_as_hex', return_value='mock_locking_script')
    @patch('service.commitment_service.TokenWallet.get_signature_scheme', return_value='NIST256p')
    @patch('service.commitment_service.TokenWallet.get_token_public_key')
    @patch('service.commitment_service.TokenWallet.sign_commitment_packet_digest', return_value=b'0x123456')
    @patch('service.commitment_service.verify_signature', return_value=True)
    @patch('service.commitment_service.Wallet.sign_tx_with_input')
    @patch('service.commitment_service.CommitmentService._broadcast_tx', return_value=Tx)
    def test_issuance_and_transfer(self, mock_broadcast, mock_sign_tx, ver_sig, mock_sig, mock_pub_key, mock_sig_scheme, mock_get_locking_script, mock_exists, mock_open):
        """ Test the creation of an issuance commitment packet
            followed by the creation of a commitment packet for transfer
            and another transfer
        """
        # Configure the mock to return different public keys for each call
        mock_pub_key.side_effect = ['mock_public_key_1', 'mock_public_key_2', 'mock_public_key_3']

        # Configure the mock to return different signatures for each call
        mock_sig.side_effect = [b'0x123456', b'0x654321']

        # Create a mock Tx object to be returned by sign_tx_with_input
        raw_tx = bytes.fromhex(
            "0100000001213fddedbbb93a5a678b69f2f884a35f655eed0c10acca29e7d6ad28206944e5000000006a47304402207b487b7dd7a87f2ae5968020f7ecc26b47d959481ee22f7c490acf64be263a6b02200c8ab50684fce2e3a3627cc84b6d502f9538b1d4bc5ba827f7e4dea2522c5dc74121024f8d67f0a5ec11e72cc0f2fa5c272b69fd448b933f92a912210f5a35a8eb2d6affffffff026cd18500000000001976a914661657ba0a6b276bb5cb313257af5cc416450c0888ac64000000000000001976a9147d981c463355c618e9666044315ef1ffc523e87088ac00000000"
        )
        tx = Tx.parse(raw_tx)
        mock_sign_tx.return_value = tx

        # Set the service finance service to the mocked version
        self.service.finance_service = self.mock_financing_service

        # Create issuance commitment
        result = self.service.create_issuance_commitment("Alice", "asset_id", "asset_data", "BSV")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid, cp) = result
        self.assertTrue(isinstance(cpid, str))
        self.assertTrue(isinstance(cp, CommitmentPacket))
        self.assertEqual(cp.asset_id, 'asset_id')
        self.assertEqual(cp.data, 'asset_data')
        self.assertEqual(cp.blockchain_id, 'BSV')
        self.assertIsNone(cp.previous_packet)

        # Create transfer template
        result = self.service.create_transfer_template(cpid, "Bob", "BSV")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid2, cp2) = result
        self.assertTrue(isinstance(cpid2, str))
        self.assertTrue(isinstance(cp2, CommitmentPacket))
        # Check ids differ
        self.assertNotEqual(cpid, cpid2)
        # Check expected data matches
        self.assertEqual(cp2.asset_id, 'asset_id')
        self.assertEqual(cp2.data, 'asset_data')
        self.assertEqual(cp2.blockchain_id, 'BSV')
        # Check linked to previous_packet
        self.assertEqual(cp2.previous_packet, cpid)
        # Check signature is not completed
        self.assertIsNone(cp2.signature)
        # Check public_key signature is completed
        self.assertNotEqual(cp2.public_key, cp.public_key)

        # Complete transfer
        result = self.service.complete_transfer(cpid2, "Alice")

        self.assertIsNotNone(result)
        assert result is not None
        (cpid3, cp3) = result
        if cp.public_key is None:
            self.fail("Public key is None")
        elif cp3.signature is None:
            self.fail("Signature is None")
        self.assertTrue(isinstance(cpid3, str))
        self.assertTrue(isinstance(cp3, CommitmentPacket))
        self.assertEqual(cp2, cp3)

        self.assertNotEqual(cpid, cpid3)
        # Check expected data matches
        self.assertEqual(cp3.asset_id, 'asset_id')
        self.assertEqual(cp3.data, 'asset_data')
        self.assertEqual(cp3.blockchain_id, 'BSV')
        # Check linked to previous_packet
        self.assertEqual(cp3.previous_packet, cpid)
        # Check signatures etc match
        self.assertNotEqual(cp3.signature, cp.signature)
        self.assertNotEqual(cp3.public_key, cp.public_key)

        # Check Commitment state
        # Can Bob transfer (no)
        self.assertFalse(self.service.can_transfer(cpid3, "Bob", is_owner=False))
        # Can Alice transfer (yes)
        self.assertTrue(self.service.can_transfer(cpid3, "Alice", is_owner=False))
        self.assertTrue(self.service.can_transfer(cpid3, "Ted", is_owner=False))

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("os.path.exists", return_value=True)
    @patch('service.commitment_service.Wallet.get_locking_script_as_hex', return_value='mock_locking_script')
    @patch('service.commitment_service.TokenWallet.get_signature_scheme', return_value='NIST256p')
    @patch('service.commitment_service.TokenWallet.get_token_public_key')
    @patch('service.commitment_service.TokenWallet.sign_commitment_packet_digest')
    @patch('service.commitment_service.verify_signature', return_value=True)
    @patch('service.commitment_service.Wallet.sign_tx_with_input')
    @patch('service.commitment_service.CommitmentService._broadcast_tx', return_value=Tx)
    def test_issuance_and_transfer_and_transfer(self, mock_broadcast, mock_sign_tx, ver_sig, mock_sig, mock_pub_key, mock_sig_scheme, mock_get_locking_script, mock_exists, mock_open):
        """ Test the creation of an issuance commitment packet
            followed by the creation of a commitment packet for transfer
            and another transfer
        """
        # Configure the mock to return different public keys for each call
        mock_pub_key.side_effect = ['mock_public_key_1', 'mock_public_key_2', 'mock_public_key_3', 'mock_public_key_4']

        # Configure the mock to return different signatures for each call
        mock_sig.side_effect = [b'0x123456', b'0x654321', b'0xabcdef']

        # Create a mock Tx object to be returned by sign_tx_with_input
        raw_tx = bytes.fromhex(
            "0100000001213fddedbbb93a5a678b69f2f884a35f655eed0c10acca29e7d6ad28206944e5000000006a47304402207b487b7dd7a87f2ae5968020f7ecc26b47d959481ee22f7c490acf64be263a6b02200c8ab50684fce2e3a3627cc84b6d502f9538b1d4bc5ba827f7e4dea2522c5dc74121024f8d67f0a5ec11e72cc0f2fa5c272b69fd448b933f92a912210f5a35a8eb2d6affffffff026cd18500000000001976a914661657ba0a6b276bb5cb313257af5cc416450c0888ac64000000000000001976a9147d981c463355c618e9666044315ef1ffc523e87088ac00000000"
        )
        tx = Tx.parse(raw_tx)
        mock_sign_tx.return_value = tx

        # Set the service finance service to the mocked version
        self.service.finance_service = self.mock_financing_service

        # Create issuance commitment
        result = self.service.create_issuance_commitment("Alice", "asset_id", "asset_data", "BSV")
        self.assertIsNotNone(result)
        (cpid, cp) = result  # type: ignore
        self.assertTrue(isinstance(cpid, str))
        self.assertTrue(isinstance(cp, CommitmentPacket))
        self.assertEqual(cp.asset_id, 'asset_id')
        self.assertEqual(cp.data, 'asset_data')
        self.assertEqual(cp.blockchain_id, 'BSV')

        self.assertIsNone(cp.previous_packet)

        # Create first transfer template (Alice -> Bob)
        result = self.service.create_transfer_template(cpid, "Bob", "BSV")
        self.assertIsNotNone(result)
        (cpid2, cp2) = result  # type: ignore
        self.assertTrue(isinstance(cpid2, str))
        self.assertTrue(isinstance(cp2, CommitmentPacket))
        self.assertNotEqual(cpid, cpid2)
        self.assertEqual(cp2.asset_id, 'asset_id')
        self.assertEqual(cp2.data, 'asset_data')
        self.assertEqual(cp2.blockchain_id, 'BSV')
        self.assertEqual(cp2.previous_packet, cpid)
        self.assertIsNone(cp2.signature)
        self.assertNotEqual(cp2.public_key, cp.public_key)

        # Complete first transfer (Alice -> Bob)
        result = self.service.complete_transfer(cpid2, "Alice")
        self.assertIsNotNone(result)
        (cpid3, cp3) = result  # type: ignore
        self.assertTrue(isinstance(cpid3, str))
        self.assertTrue(isinstance(cp3, CommitmentPacket))
        self.assertEqual(cp2, cp3)
        self.assertNotEqual(cpid, cpid3)
        self.assertEqual(cp3.asset_id, 'asset_id')
        self.assertEqual(cp3.data, 'asset_data')
        self.assertEqual(cp3.blockchain_id, 'BSV')
        self.assertEqual(cp3.previous_packet, cpid)
        self.assertNotEqual(cp3.signature, cp.signature)
        self.assertNotEqual(cp3.public_key, cp.public_key)

        # Create second transfer template (Bob -> Ted)
        result = self.service.create_transfer_template(cpid3, "Ted", "BSV")
        self.assertIsNotNone(result)
        (cpid4, cp4) = result  # type: ignore
        self.assertTrue(isinstance(cpid4, str))
        self.assertTrue(isinstance(cp4, CommitmentPacket))
        self.assertNotEqual(cpid3, cpid4)
        self.assertEqual(cp4.asset_id, 'asset_id')
        self.assertEqual(cp4.data, 'asset_data')
        self.assertEqual(cp4.blockchain_id, 'BSV')
        self.assertEqual(cp4.previous_packet, cpid3)
        self.assertIsNone(cp4.signature)

        self.assertNotEqual(cp4.public_key, cp3.public_key)

        # Complete second transfer (Bob -> Ted)
        result = self.service.complete_transfer(cpid4, "Bob")
        self.assertIsNotNone(result)
        (cpid5, cp5) = result  # type: ignore
        self.assertTrue(isinstance(cpid5, str))
        self.assertTrue(isinstance(cp5, CommitmentPacket))
        self.assertNotEqual(cpid, cpid5)
        self.assertEqual(cp5.asset_id, 'asset_id')
        self.assertEqual(cp5.data, 'asset_data')
        self.assertEqual(cp5.blockchain_id, 'BSV')
        self.assertEqual(cp5.previous_packet, cpid3)
        self.assertNotEqual(cp5.signature, cp3.signature)
        self.assertEqual(cp5.public_key, cp4.public_key)

        # Check Commitment state
        self.assertFalse(self.service.can_transfer(cpid5, "Ted", is_owner=False))
        self.assertTrue(self.service.can_transfer(cpid5, "Alice", is_owner=False))
        self.assertTrue(self.service.can_transfer(cpid5, "Bob", is_owner=False))


if __name__ == '__main__':
    unittest.main()
