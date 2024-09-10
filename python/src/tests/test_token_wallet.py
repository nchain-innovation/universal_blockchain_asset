#!/usr/bin/python3
import unittest
import sys
import hashlib
import ecdsa

sys.path.append("..")

from service.token_wallet import TokenWallet, verify_signature
from service.commitment_packet import CommitmentPacket


class TokenWalletTest(unittest.TestCase):
    """ Exercise the TokenWallet
    """
    def setUp(self):
        self.tw = TokenWallet()
        self.tw.set_key("cVvay9F4wkxrC6cLwThUnRHEajQ8FNoDEg1pbsgYjh7xYtkQ9LVZ", "SECP256k1")
        self.tw_nist256 = TokenWallet()
        self.tw_nist256.set_key("92fnTSWFiLbDvDtXNfvHByUhabdmXiv6xfy9a2zEbwqHHNbWY4z", "NIST256p")

    def test_sign_and_verify(self):
        # data to sign
        message: bytes = 'THis is a message to sign'.encode()
        sig: bytes = self.tw.sign_commitment_packet_digest(message, hashlib.sha256)
        public_key: str = self.tw.get_token_public_key()
        c: ecdsa.curves.Curve = self.tw.get_signature_curve()
        self.assertTrue(verify_signature(message, public_key, sig, c, hashlib.sha256))

    def test_sign_and_verify_with_external_hash(self):
        # data to sign
        message: bytes = """Seventeen days? Hey man, I don't wanna rain on your parade, but we're not gonna last seventeen hours! Those things are gonna come in here just like they did before. And they're gonna come in here......and they're gonna come in here AND THEY'RE GONNA KILL US!""".encode()
        hasher = hashlib.sha256()
        hasher.update(message)
        hashed_message: bytes = hasher.digest()
        sig: bytes = self.tw.sign_commitment_packet_digest(hashed_message)
        pubkey: str = self.tw.get_token_public_key()
        c: ecdsa.curves.Curve = self.tw.get_signature_curve()
        self.assertTrue(verify_signature(hashed_message, pubkey, sig, c))

    def test_sign_and_verify_failure_case(self):
        # data to sign
        message: bytes = """Seventeen days? Hey man, I don't wanna rain on your parade, but we're not gonna last seventeen hours! Those things are gonna come in here just like they did before. And they're gonna come in here......and they're gonna come in here AND THEY'RE GONNA KILL US!""".encode()
        hasher = hashlib.sha256()
        hasher.update(message)
        hashed_message: bytes = hasher.digest()
        sig: bytes = self.tw.sign_commitment_packet_digest(hashed_message)
        pubkey: str = self.tw.get_token_public_key()
        c: ecdsa.curves.Curve = self.tw.get_signature_curve()
        self.assertFalse(verify_signature(message, pubkey, sig, c))

    def test_sign_and_verify_with_nist256(self):
        message: bytes = "I say we take off and nuke the entire site from orbit. It's the only way to be sure.".encode()
        hasher = hashlib.sha256()
        hasher.update(message)
        hashed_message: bytes = hasher.digest()
        sig: bytes = self.tw_nist256.sign_commitment_packet_digest(hashed_message)
        pubkey: str = self.tw_nist256.get_token_public_key()
        cur: ecdsa.curves.Curve = self.tw_nist256.get_signature_curve()
        self.assertTrue(verify_signature(hashed_message, pubkey, sig, cur))

    def test_sign_and_verify_with_nist256_commitment_packet(self):
        cp: CommitmentPacket = CommitmentPacket(asset_id="Murphys Asset",
                                                data="Murphys_Asset_data",
                                                previous_packet="6957ca6359234cf5f7705edda20fa21039a6c1124d216cbc4ab6b5b298eeaacd",
                                                blockchain_outpoint="6e59cf55510fb810ae51e2948ae27055559e6795f56c85a2c8c7171eac98ed48:1",
                                                blockchain_id="BSV",
                                                signature="",
                                                signature_scheme="",
                                                public_key=""
                                                )  # type: ignore[call-arg]

        cp.public_key = self.tw_nist256.get_token_public_key()
        cp.signature_scheme = self.tw_nist256.get_signature_scheme()

        message: bytes = cp.packet_digest()
        hasher = hashlib.sha256()
        hasher.update(message)
        hashed_message: bytes = hasher.digest()
        sig: bytes = self.tw_nist256.sign_commitment_packet_digest(hashed_message)
        c: ecdsa.curves.Curve = self.tw_nist256.get_signature_curve()
        self.assertTrue(verify_signature(hashed_message, cp.public_key, sig, c))


if __name__ == "__main__":
    unittest.main()
