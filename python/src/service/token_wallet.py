import ecdsa
from config import ConfigType
from tx_engine import wif_to_bytes

class TokenWallet:
    """ This class represents the Wallet functionality for token signing
    """
    def __init__(self):
        self.private_key: ecdsa.SigningKey
        self.curve: ecdsa.Curve

    def set_config(self, config: ConfigType):
        """ Given the wallet configuration, set up the wallet
        """
        # Keys and addresses
        wif_key_str = config["token_key"]
        secret_exponent = int.from_bytes(wif_to_bytes(wif_key_str), byteorder='big')
        token_curve_str: str = config["token_key_curve"]
        self.signature_scheme = config["token_key_curve"]

        self.curve = ecdsa.curves.curve_by_name(token_curve_str)
        self.private_key = ecdsa.SigningKey.from_secret_exponent(secret_exponent, curve=self.curve)

    def set_key(self, token_key: str, token_key_curve: str):
        self.signature_scheme = token_key_curve
        self.curve = ecdsa.curves.curve_by_name(token_key_curve)
        secret_exponent = int.from_bytes(wif_to_bytes(token_key), byteorder='big')
        self.private_key = ecdsa.SigningKey.from_secret_exponent(secret_exponent, curve=self.curve)

    def sign_commitment_packet_digest(self, digest_to_sign: bytes, hashfunction=None) -> bytes:
        signature = self.private_key.sign(digest_to_sign, hashfunc=hashfunction)
        return signature

    def get_token_public_key_bytes(self) -> bytes:
        return self.private_key.get_verifying_key().to_string()

    def get_token_public_key_pem(self) -> str:
        return self.private_key.get_verifying_key().to_pem().hex()

    def get_token_public_key(self) -> str:
        return self.private_key.get_verifying_key().to_string(encoding="compressed").hex()

    def get_signature_scheme(self) -> str:
        return self.curve.name

    def get_signature_curve(self) -> ecdsa.curves.Curve:
        return self.curve


def verify_signature_pem(message: bytes, publickey: str, sig: bytes, hashfunction=None) -> bool:
    vk: ecdsa.VerifyingKey = ecdsa.VerifyingKey.from_pem(bytes.fromhex(publickey))
    try:
        if vk.verify(sig, message, hashfunc=hashfunction):
            return True
        return False
    except ecdsa.BadSignatureError:
        return False


def verify_signature(message: bytes, publickey: str, sig: bytes, selected_curve: ecdsa.curves.Curve = ecdsa.curves.NIST256p, hashfunction=None) -> bool:

    vk: ecdsa.VerifyingKey = ecdsa.VerifyingKey.from_string(bytes.fromhex(publickey), curve=selected_curve)
    try:
        if vk.verify(sig, message, hashfunc=hashfunction):
            return True
        return False
    except ecdsa.BadSignatureError:
        return False
