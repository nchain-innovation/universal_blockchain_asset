
if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.join(sys.path[0], ".."))
    from commitment_packet import CommitmentPacketMetadata, CommitmentPacket, CommitmentStatus, Cpid, CommitmentType
    from service.util import is_unit_test
else:
    from service.commitment_packet import CommitmentPacketMetadata, CommitmentPacket, CommitmentStatus, Cpid, CommitmentType
    from service.util import is_unit_test

import json
from typing import List, Tuple

from config import ConfigType


class CommitmentStore:
    def __init__(self):
        self.filepath: str = ""
        self.commitments: List[CommitmentPacketMetadata] = []

    def set_config(self, config: ConfigType):
        self.filepath = config["commitment_store"]["filepath"]

    def save(self) -> bool:
        # Convert to something we can write out
        serialisable_commitments = [c.model_dump() for c in self.commitments]
        with open(self.filepath, 'w') as f:
            json.dump(serialisable_commitments, f, indent=4)
        return True

    def load(self) -> bool:
        print("Loading commitments from", self.filepath)
        try:
            with open(self.filepath, 'r') as f:
                serial_data = json.load(f)
            self.commitments = [CommitmentPacketMetadata.model_validate(cp) for cp in serial_data]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Got fed up of this printing during unit tests
            if not is_unit_test():
                print(e)
            return False
        return True

    def reset(self):
        """ Erase all stored info - for testing
        """
        self.commitments = []

    def get_metadata_by_cpid(self, cpid: str) -> None | CommitmentPacketMetadata:
        for cp_meta in self.commitments:
            if cp_meta.commitment_packet_id == cpid:
                return cp_meta
        return None

    def get_index_by_cpid(self, cpid: str) -> None | int:
        for (i, cp_meta) in enumerate(self.commitments):
            if cp_meta.commitment_packet_id == cpid:
                return i
        return None

    def get_commitment_by_cpid(self, cpid: str) -> None | CommitmentPacket:
        cp_meta = self.get_metadata_by_cpid(cpid)
        if cp_meta is not None:
            return cp_meta.commitment_packet
        return None

    def get_commitment_history(self, cpid: str) -> List[Tuple[Cpid, CommitmentPacket]]:
        history = []
        current_cpid = cpid

        while current_cpid is not None:
            cp_meta = self.get_metadata_by_cpid(current_cpid)
            if cp_meta is None:
                break
            history.append((current_cpid, cp_meta.commitment_packet))
            current_cpid = cp_meta.commitment_packet.previous_packet

        return history

    def get_commitments_by_actor(self, actor: str) -> List[Tuple[Cpid, CommitmentPacket]]:
        return [(c.commitment_packet_id, c.commitment_packet) for c in self.commitments if c.owner == actor]

    def get_commitments_by_actor_without_spending_tx(self, actor: str) -> List[Tuple[Cpid, CommitmentPacket]]:
        return [(c.commitment_packet_id, c.commitment_packet) for c in self.commitments if c.owner == actor and c.spending_tx is None]

    def _is_owner(self, actor: str, cpid: str) -> bool:
        meta = self.get_metadata_by_cpid(cpid)
        assert meta is not None
        return meta.owner == actor

    def get_transfers_by_actor(self, actor: str) -> List[Cpid]:
        """ Get Commitment Transfers of this actor's Commitments
        """
        # Find all transfer packets that have not been completed
        # Check to see if actor held previous packet
        # If so record transfer packet
        return [
            [c.commitment_packet_id, c.commitment_packet] for c in self.commitments
            if c.owner != actor and c.type == CommitmentType.Transfer and c.state == CommitmentStatus.Created and c.commitment_packet.signature is None and self._is_owner(actor, c.commitment_packet.previous_packet)
        ]

    def add_commitment(self, cp_meta: CommitmentPacketMetadata):
        self.commitments.append(cp_meta)
        self.save()

    def update_commitment(self, cp_meta: CommitmentPacketMetadata):
        i = self.get_index_by_cpid(cp_meta.commitment_packet_id)
        assert i is not None
        self.commitments[i] = cp_meta
        self.save()

    def is_commitment_unique(self, asset_id: str, asset_data: str, network: str) -> bool:
        return not any(map(lambda x: x.is_match(asset_id, asset_data, network, CommitmentStatus.Created), self.commitments))

    def is_known_cpid(self, cpid: str) -> bool:
        return any(map(lambda x: x.commitment_packet_id == cpid, self.commitments))

    def can_transfer(self, cpid: str, actor: str, is_owner: bool) -> bool:
        for cp_meta in self.commitments:
            # Found packet
            if cp_meta.commitment_packet_id == cpid:
                # Cannot transfer transferred packet - that is a packet in transferred state
                if cp_meta.state != CommitmentStatus.Created:
                    return False
                # Cannot transfer to self
                if cp_meta.owner == actor:
                    return is_owner
                else:
                    return not is_owner
        # Didn't find packet
        return False

    def can_complete_transfer(self, cpid: str, actor: str) -> bool:
        for cp_meta in self.commitments:
            # Found packet
            if cp_meta.commitment_packet_id == cpid:
                # Cannot transfer transferred packet - that is a packet in transferred state
                if cp_meta.state != CommitmentStatus.Created:
                    return False
                # Cannot transfer to self
                if cp_meta.owner == actor:
                    return False
                else:
                    # Now we need to check that the previous commitment is valid
                    orignal_cpid = cp_meta.commitment_packet.previous_packet
                    if orignal_cpid is None:
                        return False
                    else:
                        return self.can_transfer(orignal_cpid, actor, is_owner=True)
        # Didn't find packet
        return False


if __name__ == '__main__':
    cs = CommitmentStore()
    config = {
        "commitment_store": {
            "filepath": os.path.join(os.path.dirname(__file__), "../data/commitments.json")
        }
    }
    cs.set_config(config)
    cs.load()

    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(cs.commitments)
    cp = cs.commitments[0]

    print(type(cp))
