#!/usr/bin/python3
import unittest
from unittest.mock import patch, mock_open
import sys
sys.path.append("..")

import pprint
pp = pprint.PrettyPrinter()

from service.commitment_packet import CommitmentPacket, CommitmentPacketMetadata
from service.commitment_service import CommitmentService
from service.token_description import token_store
from tx_engine import MockInterface

from mock_financing_service import MockFinancingService

COMMITMENT_STORE_FILE = '../../data/test-commitments.json'
TOKEN_FILE_STORE = '../../data/token_store.json'

CONFIG = {
    'actor': [
        {'name': 'Alice',
            'token_key': '91tohTNiSH4newk8q8X6D4zZ36xABwG7MWUC9KTJHUvJZVBoLo3',
            'token_key_curve': 'NIST256p',
            'bitcoin_key': 'cVvay9F4wkxrC6cLwThUnRHEajQ8FNoDEg1pbsgYjh7xYtkQ9LVZ',
            'eth_key': '57afe53e85961095022411ab379e3a4a73d30b9ee1684b2b1979715c2d67a0bd'},
        {'name': 'Bob',
            'token_key': '91ppjc4SCw8AFyAS8o7UzaD793M4dnExKwJ13f28WMek9KhUhmn',
            'token_key_curve': 'NIST256p',
            'bitcoin_key': 'cP1oascUTcrkYf9Ws9XkfESaL7yKJA8a3fxxT3D57gubDD6Va51D',
            'eth_key': '8dcc9c34d6bf487b9cde8f58c78b3a61aca39c248f45a8a21f6a2118040d28de'},
        {'name': 'Ted',
            'token_key': '92Gbcgn1L6LNisT6ztuFEa41QAynpmdJD7U9DBNRDT2BJxP1deE',
            'token_key_curve': 'NIST256p',
            'bitcoin_key': 'cNCvcVZ7tespNwKywAELCgyCQqoQExpzDPccaMFj3zDE1MZPRDPx',
            'eth_key': '8ac317c9ad1af866bdd18cf2b52733eaa34cd969269c78dcf2365c46b0399074'},
    ],
    'blockchain': {
        'interface': 'woc',
            'network': 'testnet',
            'type': 'testnet',
            'interface_type': 'mock',
            'uaas_address': 'http://127.0.0.1:5010',
            'uaas_collections': ['commitment']
    },
    'commitment_service': {
        'blockchain_enabled': True,
        'ethereum_enabled': False,
        'networks': ['BSV', 'ETH']
    },
    'ethereum_service': {
        'ethNodeUrl': 'https://sepolia.infura.io/v3/',
        'apiKey': '25810eab24f5460ca96527cffa737d4f',
        'gas': '2000000',
        'gasPrice': '20000000000',
        'maxGasPrice': '20000000000'
    },
    'commitment_store': {
        'filepath': COMMITMENT_STORE_FILE
    },
    'finance_service': {
        'client_id': 'commitment',
        'url': 'http://host.docker.internal:8070',
        'utxo_cache_enabled': False,
        'utxo_file': '../data/utxo.json',
        'utxo_min_level': 10,
        'utxo_persistence_enabled': False,
        'utxo_request_level': 5
    },
    "uaas": {
        "service_url": "http://host.docker.internal:5010",
        "collections": ["commitment"],
    },
    'token_info': {
        'token_file_store': TOKEN_FILE_STORE
    },
    'token': [{'ipfs_cid': 'asset_data', 'description': 'asset description'}]
}

FUNDS = [
    "0100000001baa9ec5094816f5686371e701b3a4dcadc93df44d151496a58089018706b865c000000006b483045022100b53c9ab501032a626050651fb785967e1bdf03bca0cb17cb4f2c75a45a56d17d0220292a27ce9001efb9c41ab9a06ecaaefad91138e94d4407ee14952456274357a24121024f8d67f0a5ec11e72cc0f2fa5c272b69fd448b933f92a912210f5a35a8eb2d6affffffff0276198900000000001976a914661657ba0a6b276bb5cb313257af5cc416450c0888ac64000000000000001976a9147d981c463355c618e9666044315ef1ffc523e87088ac00000000",
    "0100000001039c459f8538aa0f659a34aac529934c2448786d889c5b3fa49f22cad363d7b8000000006b483045022100b4e088e0528afdd71381362d96445bc7657c5e27348d33d570bf3739ef05efd7022059e44340f10a9b6b3c2c20ab32fe262e918c19da267436cbe37f43eb74cb788b4121024f8d67f0a5ec11e72cc0f2fa5c272b69fd448b933f92a912210f5a35a8eb2d6affffffff0224168900000000001976a914661657ba0a6b276bb5cb313257af5cc416450c0888ac64000000000000001976a91439247d1ce46d257134c800ffe2e77cada49a511c88ac00000000",
]


class TestCommitmentService(unittest.TestCase):
    """ Exercise the CommitmentService
    """
    def setUp(self):

        # Mock bsv client
        self.mock_bsv_client = MockInterface()
        # Set up network
        self.mock_bsv_client.set_transactions({})
        self.mock_bsv_client.clear_broadcast_txs()
        self.mock_bsv_client.set_utxo({})

        # Setup financing service
        self.mock_financing_service = MockFinancingService(self.mock_bsv_client, FUNDS)
        # Set up service
        self.cs = CommitmentService()
        self.cs.set_config(CONFIG)
        self.cs.blockchain_interface = self.mock_bsv_client
        self.cs.finance_service = self.mock_financing_service  # type: ignore[assignment]
        token_store.set_config(CONFIG)

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("os.path.exists", return_value=True)
    def test_issuance(self, mock_exists, mock_open):
        """ Test the creation of an issuance commitment packet
        """
        result = self.cs.create_issuance_commitment("Alice", "asset_id", "asset_data", "BSV")
        # print(f"result = {result}")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid, cp) = result
        self.assertTrue(isinstance(cpid, str))
        self.assertTrue(isinstance(cp, CommitmentPacket))

        # Check tx
        self.assertEqual(len(self.mock_bsv_client.broadcast), 1)
        txid = list(self.mock_bsv_client.broadcast.keys())[0]
        self.assertEqual(cp.blockchain_outpoint, txid + ":1")

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("os.path.exists", return_value=True)
    def test_issuance_and_template(self, mock_exists, mock_open):
        """ Test the creation of an issuance commitment packet
            followed by the creation of a cpmmitment packet for transfer
        """
        result = self.cs.create_issuance_commitment("Alice", "asset_id", "asset_data", "BSV")
        # print(f"result1 = {result}")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid, cp) = result
        self.assertTrue(isinstance(cpid, str))
        self.assertTrue(isinstance(cp, CommitmentPacket))

        # Check tx
        self.assertEqual(len(self.mock_bsv_client.broadcast), 1)
        txid = list(self.mock_bsv_client.broadcast.keys())[0]
        self.assertEqual(cp.blockchain_outpoint, txid + ":1")

        result = self.cs.create_transfer_template(cpid, "Bob", "BSV")
        # print(f"result2 = {result}")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid2, cp2) = result
        self.assertTrue(isinstance(cpid2, str))
        self.assertTrue(isinstance(cp2, CommitmentPacket))

        # Check tx - addtional ownership tx broadcast
        self.assertEqual(len(self.mock_bsv_client.broadcast), 2)
        txid = list(self.mock_bsv_client.broadcast.keys())[1]
        self.assertEqual(cp2.blockchain_outpoint, txid + ":1")

    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    @patch("os.path.exists", return_value=True)
    def test_issuance_and_transfer(self, mock_exists, mock_open):
        """ Test the creation of an issuance commitment packet
            followed by the creation of a commitment packet for transfer
            and the completition of the transfer
        """
        result = self.cs.create_issuance_commitment("Alice", "asset_id", "asset_data", "BSV")
        # print(f"result1 = {result}")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid, cp) = result
        self.assertTrue(isinstance(cpid, str))
        self.assertTrue(isinstance(cp, CommitmentPacket))

        result = self.cs.create_transfer_template(cpid, "Bob", "BSV")
        # print(f"result2 = {result}")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid2, cp2) = result
        self.assertTrue(isinstance(cpid2, str))
        self.assertTrue(isinstance(cp2, CommitmentPacket))

        result = self.cs.complete_transfer(cpid2, "Alice")
        # print(f"result3 = {result}")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid3, cp3) = result
        self.assertTrue(isinstance(cpid3, str))
        self.assertTrue(isinstance(cp3, CommitmentPacket))

        # Check tx - addtional spending_tx broadcast
        self.assertEqual(len(self.mock_bsv_client.broadcast), 3)
        meta_cp = self.cs.get_commitment_meta_by_cpid(cpid)
        broadcast_txs = list(self.mock_bsv_client.broadcast.values())
        assert isinstance(meta_cp, CommitmentPacketMetadata)
        self.assertEqual(meta_cp.ownership_tx, broadcast_txs[0])
        self.assertEqual(meta_cp.spending_tx, broadcast_txs[2])


if __name__ == "__main__":
    unittest.main()
