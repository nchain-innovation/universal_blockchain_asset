#!/usr/bin/python3
import unittest
import os
import sys
import hashlib
import ecdsa
sys.path.append("..")

from service.commitment_packet import CommitmentPacket
from service.commitment_service import CommitmentService
from service.token_description import token_store
from service.token_wallet import verify_signature


COMMITMENT_STORE_FILE = '../../data/test-commitments.json'
TOKEN_FILE_STORE = '../../data/token_store.json'

CONFIG = {
    'actor': [
        {'name': 'Alice',
            'token_key': '91tohTNiSH4newk8q8X6D4zZ36xABwG7MWUC9KTJHUvJZVBoLo3',
            'token_key_curve': 'NIST256p',
            'bitcoin_key': 'cVvay9F4wkxrC6cLwThUnRHEajQ8FNoDEg1pbsgYjh7xYtkQ9LVZ'},
        {'name': 'Bob',
            'token_key': '91ppjc4SCw8AFyAS8o7UzaD793M4dnExKwJ13f28WMek9KhUhmn',
            'token_key_curve': 'NIST256p',
            'bitcoin_key': 'cP1oascUTcrkYf9Ws9XkfESaL7yKJA8a3fxxT3D57gubDD6Va51D'},
        {'name': 'Ted',
            'token_key': '92Gbcgn1L6LNisT6ztuFEa41QAynpmdJD7U9DBNRDT2BJxP1deE',
            'token_key_curve': 'NIST256p',
            'bitcoin_key': 'cNCvcVZ7tespNwKywAELCgyCQqoQExpzDPccaMFj3zDE1MZPRDPx'}
    ],
    'commitment_service': {
        'blockchain_enabled': False,
        'ethereum_enabled': False,
        'networks': ['BSV', 'ETH']
    },
    'commitment_store': {
        'filepath': COMMITMENT_STORE_FILE
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


class CommitmentServiceTests(unittest.TestCase):
    """ Exercise the CommitmentService
    """
    def setUp(self):
        if True:
            try:
                os.remove(COMMITMENT_STORE_FILE)
            except FileNotFoundError:
                pass

        self.cs = CommitmentService()
        self.cs.set_config(CONFIG)
        token_store.set_config(CONFIG)

    def test_actors(self):
        self.assertTrue(self.cs.is_known_actor("Alice"))
        self.assertTrue(self.cs.is_known_actor("Ted"))
        self.assertTrue(self.cs.is_known_actor("Bob"))
        self.assertFalse(self.cs.is_known_actor("Murphy"))

        self.assertNotEqual(self.cs.actors_token_wallets["Alice"].get_token_public_key(), self.cs.actors_token_wallets["Ted"].get_token_public_key())
        self.assertNotEqual(self.cs.actors_token_wallets["Ted"].get_token_public_key(), self.cs.actors_token_wallets["Bob"].get_token_public_key())
        self.assertNotEqual(self.cs.actors_token_wallets["Bob"].get_token_public_key(), self.cs.actors_token_wallets["Alice"].get_token_public_key())

    def test_networks(self):
        self.assertTrue(self.cs.is_known_network("BSV"))
        self.assertFalse(self.cs.is_known_network("BTC"))

    def test_issuance(self):
        """ Test the creation of an issuance commitment packet
        """
        result = self.cs.create_issuance_commitment("Alice", "asset_id", "asset_data", "BSV")
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
        self.assertTrue(self.cs.can_transfer(cpid, "Bob", is_owner=False))
        self.assertTrue(self.cs.can_transfer(cpid, "Ted", is_owner=False))
        # Can Alice transfer (no)
        self.assertFalse(self.cs.can_transfer(cpid, "Alice", is_owner=False))

        # Can Alice complete the transfer? (no)
        self.assertFalse(self.cs.can_complete_transfer(cpid, "Alice"))
        self.assertFalse(self.cs.can_complete_transfer(cpid, "Bob"))

    def test_issuance_and_template(self):
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

        result = self.cs.create_transfer_template(cpid, "Bob", "BSV")
        # print(f"result2 = {result}")
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
        self.assertTrue(self.cs.can_complete_transfer(cpid2, "Alice"))
        # Can Bob complete the transfer? (no)
        self.assertFalse(self.cs.can_complete_transfer(cpid2, "Bob"))
        self.assertFalse(self.cs.can_complete_transfer(cpid2, "Ted"))
        self.assertFalse(self.cs.can_complete_transfer(cpid2, "Fred"))

    def test_issuance_and_transfer(self):
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
        # verify the signature
        c: ecdsa.curves.Curve = ecdsa.curves.curve_by_name(cp3.signature_scheme)
        if cp.public_key is None:
            self.fail("Public key is None")
        elif cp3.signature is None:
            self.fail("Signature is None")
        else:
            self.assertTrue(verify_signature(cp3.packet_digest(), cp.public_key, bytes.fromhex(cp3.signature), c, hashlib.sha256))
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
        self.assertFalse(self.cs.can_transfer(cpid3, "Bob", is_owner=False))
        # Can Alice transfer (yes)
        self.assertTrue(self.cs.can_transfer(cpid3, "Alice", is_owner=False))
        self.assertTrue(self.cs.can_transfer(cpid3, "Ted", is_owner=False))

    def test_issuance_and_transfer_and_transfer(self):
        """ Test the creation of an issuance commitment packet
            followed by the creation of a commitment packet for transfer
            and the completion of the transfer
            and transfer again
        """
        result = self.cs.create_issuance_commitment("Alice", "asset_id", "asset_data", "BSV")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid, cp) = result
        self.assertTrue(isinstance(cpid, str))
        self.assertTrue(isinstance(cp, CommitmentPacket))

        # Transfer Alice -> Bob
        result = self.cs.create_transfer_template(cpid, "Bob", "BSV")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid2, cp2) = result
        self.assertTrue(isinstance(cpid2, str))
        self.assertTrue(isinstance(cp2, CommitmentPacket))

        result = self.cs.complete_transfer(cpid2, "Alice")
        # verify the signature
        curve1: ecdsa.curves.Curve = ecdsa.curves.curve_by_name(cp2.signature_scheme)
        if cp.public_key is None or cp2.signature is None:
            self.fail("Public key or signature is None")
        else:
            self.assertTrue(verify_signature(cp2.packet_digest(), cp.public_key, bytes.fromhex(cp2.signature), curve1, hashlib.sha256))

        self.assertIsNotNone(result)
        assert result is not None
        (cpid3, cp3) = result
        # verify the signature
        curve2: ecdsa.curves.Curve = ecdsa.curves.curve_by_name(cp3.signature_scheme)
        if cp.public_key is None or cp3.signature is None:
            self.fail("Public key or signature is None")
        else:
            self.assertTrue(verify_signature(cp3.packet_digest(), cp.public_key, bytes.fromhex(cp3.signature), curve2, hashlib.sha256))

        self.assertTrue(isinstance(cpid3, str))
        self.assertTrue(isinstance(cp3, CommitmentPacket))
        self.assertEqual(cpid2, cpid3)
        self.assertEqual(cp2, cp3)
        self.assertNotEqual(cpid, cpid3)

        # Transfer Bob -> Ted
        result = self.cs.create_transfer_template(cpid2, "Ted", "BSV")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid4, cp4) = result
        self.assertTrue(isinstance(cpid4, str))
        self.assertTrue(isinstance(cp4, CommitmentPacket))
        result = self.cs.complete_transfer(cpid4, "Bob")
        # print(f"result3 = {result}")
        self.assertIsNotNone(result)
        assert result is not None
        (cpid5, cp5) = result
        self.assertTrue(isinstance(cpid5, str))
        self.assertTrue(isinstance(cp5, CommitmentPacket))

        self.assertNotEqual(cpid, cpid5)

        # Check expected data matches
        self.assertEqual(cp5.asset_id, 'asset_id')
        self.assertEqual(cp5.data, 'asset_data')
        self.assertEqual(cp5.blockchain_id, 'BSV')
        # Check linked to previous_packet
        self.assertEqual(cp5.previous_packet, cpid3)
        # Check signatures etc match
        self.assertNotEqual(cp5.signature, cp3.signature)
        self.assertEqual(cp5.public_key, cp4.public_key)

        # Check Commitment state
        # Can Bob transfer (no)
        self.assertFalse(self.cs.can_transfer(cpid5, "Ted", is_owner=False))
        # Can Alice transfer (yes)
        self.assertTrue(self.cs.can_transfer(cpid5, "Alice", is_owner=False))
        self.assertTrue(self.cs.can_transfer(cpid5, "Bob", is_owner=False))


if __name__ == "__main__":
    unittest.main()
