#!/usr/bin/python3
import unittest
from unittest.mock import patch, mock_open
import os
import sys
sys.path.append("..")

from service.commitment_store import CommitmentStore
from tx_engine import Tx, TxIn
from service.commitment_packet import CommitmentPacket, CommitmentPacketMetadata, CommitmentStatus, CommitmentType, Cpid
from service.util import tx_to_hexstr


COMMITMENT_STORE_FILE = '../../data/test-commitments.json'

CONFIG = {
    'actor': [
        {'name': 'Alice',
            'token_key': 'cVvay9F4wkxrC6cLwThUnRHEajQ8FNoDEg1pbsgYjh7xYtkQ9LVZ',
            'token_key_curve': 'SECP256k1',
            'wif_key': 'cVvay9F4wkxrC6cLwThUnRHEajQ8FNoDEg1pbsgYjh7xYtkQ9LVZ'},
        {'name': 'Bob',
            'token_key': 'cP1oascUTcrkYf9Ws9XkfESaL7yKJA8a3fxxT3D57gubDD6Va51D',
            'token_key_curve': 'SECP256k1',
            'wif_key': 'cP1oascUTcrkYf9Ws9XkfESaL7yKJA8a3fxxT3D57gubDD6Va51D'},
        {'name': 'Ted',
            'token_key': 'cNCvcVZ7tespNwKywAELCgyCQqoQExpzDPccaMFj3zDE1MZPRDPx',
            'token_key_curve': 'SECP256k1',
            'wif_key': 'cNCvcVZ7tespNwKywAELCgyCQqoQExpzDPccaMFj3zDE1MZPRDPx'}
    ],
    'commitment_service': {
        'blockchain_enabled': False,
        'networks': ['BSV', 'ETH']
    },
    'commitment_store': {
        'filepath': COMMITMENT_STORE_FILE
    },
}


class CommitmentStoreTests(unittest.TestCase):
    """ Exercise the Commitment Store
    """
    def setUp(self):
        if True:
            try:
                os.remove(COMMITMENT_STORE_FILE)
            except FileNotFoundError:
                pass

        self.cs = CommitmentStore()
        self.cs.set_config(CONFIG)

    @patch("builtins.open", new_callable=mock_open, read_data='[]')
    @patch("os.path.exists", return_value=True)
    def test_load(self, mock_exists, mock_open):
        self.cs.load()
        self.assertEqual(self.cs.commitments, [])

    @patch("builtins.open", new_callable=mock_open, read_data='[]')
    @patch("os.path.exists", return_value=True)
    def test_save_and_load(self, mock_exists, mock_open):
        # Create Issuance Commitment Packet
        actor = "Alice"
        network = "BSV"
        asset_id = "person"
        asset_data = "Murphy"

        vin = TxIn(prev_tx="00000000000000000000000000000000", prev_index=0)
        utxo_tx = Tx(1, [], [], 0)

        # Create commitment packet
        cp = CommitmentPacket(
            asset_id=asset_id,
            data=asset_data,
            previous_packet=None,
            blockchain_outpoint=str(vin),
            blockchain_id=network,
            signature="",
            signature_scheme="",
            public_key=""
        )  # type: ignore[call-arg]

        # Store commitment packet
        cpid = Cpid("test_cpid")
        cp_meta = CommitmentPacketMetadata(
            owner=actor,
            type=CommitmentType.Issuance,
            state=CommitmentStatus.Created,
            ownership_tx=tx_to_hexstr(utxo_tx),
            spending_tx="",
            commitment_packet_id=cpid,
            commitment_packet=cp
        )
        self.cs.add_commitment(cp_meta)
        self.cs.save()

        # Mock the file read to return the saved data
        mock_open().read.return_value = '[{"owner": "Alice", "type": "Issuance", "state": "Created", "ownership_tx": "01000000000000000000", "spending_tx": "", "commitment_packet_id": "test_cpid", "commitment_packet": {"asset_id": "person", "data": "Murphy", "previous_packet": null, "signature": "", "signature_scheme": "", "public_key": "", "blockchain_outpoint": "PyTxIn { prev_tx: \\"00000000000000000000000000000000\\", prev_index: 0, sequence: 4294967295, script_sig: \\"\\" }", "blockchain_id": "BSV"}}]'
        self.cs.reset()
        self.assertEqual(self.cs.commitments, [])
        
        self.cs.load()

        CP_META = CommitmentPacketMetadata(
            owner='Alice',
            type=CommitmentType.Issuance,
            state=CommitmentStatus.Created,
            ownership_tx=tx_to_hexstr(utxo_tx),
            spending_tx="",
            commitment_packet_id=Cpid('test_cpid'),
            commitment_packet=CommitmentPacket(
                asset_id='person',
                data='Murphy',
                previous_packet=None,
                signature="",
                signature_scheme="",
                public_key="",
                blockchain_outpoint=str(vin),
                blockchain_id='BSV'
            )
        )
        self.assertEqual(self.cs.commitments, [CP_META])


if __name__ == "__main__":
    unittest.main()
