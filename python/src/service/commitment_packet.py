from pydantic import BaseModel, validator
from enum import Enum
import hashlib


from typing import NewType, Tuple
Cpid = NewType("Cpid", str)


class CommitmentPacket(BaseModel):
    """ Store information about Commitment Packet
    """
    asset_id: str
    data: str
    # Input
    previous_packet: None | str
    signature: None | str
    signature_scheme: None | str

    # Output
    public_key: None | str
    blockchain_outpoint: None | str
    blockchain_id: str

    @validator('previous_packet', 'signature', 'signature_scheme', 'public_key', 'blockchain_outpoint', pre=True)
    def replace_null_with_none(cls, v):
        return v if isinstance(v, str) else None

    def is_match(self, asset_id: str, asset_data: str, network: str) -> bool:
        """ Quick check to see if two packets match
        """
        return self.asset_id == asset_id and self.data == asset_data and self.blockchain_id == network

    def get_cpid(self) -> Cpid:
        """ Calculate the Commitment Packet hash to create CPID
            including previous_packet (where avalible)
            excluding the signature
        """
        assert self.signature_scheme is not None
        assert self.public_key is not None
        assert self.blockchain_outpoint is not None
        # self.signature - Note signature is not part of the ID
        if self.previous_packet is not None:
            input = bytes(self.asset_id + self.data + self.blockchain_id + self.signature_scheme + self.public_key + self.previous_packet + self.blockchain_outpoint, 'utf-8')
        else:
            input = bytes(self.asset_id + self.data + self.blockchain_id + self.signature_scheme + self.public_key + self.blockchain_outpoint, 'utf-8')
        return Cpid(hashlib.sha256(input).digest().hex())

    def packet_digest(self) -> bytes:
        """ Return data to hash for signing
        """
        cp_digest: bytes = bytes()
        cp_digest = bytes(self.asset_id, 'utf-8')
        if self.data is not None:
            cp_digest += bytes(self.data, 'utf-8')
        if self.previous_packet is not None:
            cp_digest += bytes(self.previous_packet, 'utf-8')

        assert self.public_key is not None
        assert self.blockchain_outpoint is not None
        assert self.blockchain_id is not None

        cp_digest += bytes(self.public_key, 'utf-8')
        cp_digest += bytes(self.blockchain_outpoint, 'utf-8')
        cp_digest += bytes(self.blockchain_id, 'utf-8')
        return cp_digest

    def get_blockchain_txid(self) -> None | str:
        """ Return the ownership txid
        """
        match self.blockchain_id:
            case "BSV":
                if self.blockchain_outpoint is None:
                    return None
                else:
                    input = self.blockchain_outpoint.split(':')
                    return input[0]
            case _:
                raise NotImplementedError(f"Unknown blockchain {self.blockchain_id}")

    def get_blockchain_txid_and_index(self) -> None | Tuple[str, int]:
        """ Return the ownership txid and index
        """
        match self.blockchain_id:
            case "BSV":
                if self.blockchain_outpoint is None:
                    return None
                else:
                    input = self.blockchain_outpoint.split(':')
                    return (input[0], int(input[1]))
            case _:
                raise NotImplementedError(f"Unknown blockchain {self.blockchain_id}")


class CommitmentStatus (str, Enum):
    Created = "Created"
    Transferred = "Transferred"

    def __repr__(self):
        return self.value


class CommitmentType (str, Enum):
    Issuance = "Issuance"
    Transfer = "Transfer"

    def __repr__(self):
        return self.value


class CommitmentPacketMetadata(BaseModel):
    """ Store commitment packet metadata
    """
    owner: str
    type: CommitmentType
    state: CommitmentStatus
    ownership_tx: None | str
    spending_tx: None | str
    commitment_packet_id: None | Cpid
    commitment_packet: CommitmentPacket

    @validator('ownership_tx', 'spending_tx', 'commitment_packet_id', pre=True)
    def replace_null_with_none(cls, v):
        return v if isinstance(v, str) else None

    # TODO: review is match
    def is_match(self, asset_id: str, asset_data: str, network: str, state: CommitmentStatus) -> bool:
        return self.commitment_packet.is_match(asset_id, asset_data, network) and self.state == state
