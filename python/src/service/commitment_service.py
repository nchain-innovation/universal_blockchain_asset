import pprint
import hashlib
import sys
import ecdsa

from typing import NewType, Tuple, Any, Dict, List, Optional
pp = pprint.PrettyPrinter()
from config import ConfigType

from tx_engine import interface_factory
from tx_engine import Tx, TxIn, TxOut, Script


from service.commitment_packet import CommitmentPacket, CommitmentPacketMetadata, CommitmentStatus, Cpid, CommitmentType
from service.financing_service import FinancingService, FinancingServiceException
from service.wallet import Wallet
from service.token_wallet import TokenWallet, verify_signature
from service.commitment_store import CommitmentStore
from service.util import hexstr_to_tx, tx_to_hexstr, hexstr_to_txin, hexstr_to_txid
from ethereum.ethereum_wallet import EthereumWallet
from ethereum.ethereum_service import EthereumService

from service.token_description import token_store
Txid = NewType("Txid", str)


# <TODO> how / where do we call the ethereum txSpentStatus function?
class CommitmentService:
    """ A  service for creating commitment tokens
    """
    def __init__(self):
        self.finance_service = FinancingService()
        self.actors_wallets: Dict[str, Wallet] = {}
        self.actors_token_wallets: Dict[str, TokenWallet] = {}
        self.actors_eth_wallets: Dict[str, EthereumWallet] = {}
        self.networks: List[str] = []
        self.commitment_store: CommitmentStore = CommitmentStore()
        self.ethereum_service: EthereumService = EthereumService()

    def set_actors(self, config: ConfigType):
        """ Read the actors from the configuration and validate their keys
        """
        try:
            for actor in config["actor"]:
                name = actor['name']
                bitcoin_key = actor.get('bitcoin_key')
                token_key = actor.get('token_key')
                token_key_curve = actor.get('token_key_curve')
                eth_key = actor.get('eth_key')

                # Check if the required keys are set
                if not bitcoin_key:
                    raise ValueError(f"Bitcoin key for {name} is not set")
                if not token_key:
                    raise ValueError(f"Token key for {name} is not set")
                if not token_key_curve:
                    raise ValueError(f"Token key curve for {name} is not set")
                if not eth_key:
                    raise ValueError(f"Ethereum key for {name} is not set")

                wallet = Wallet()
                try:
                    wallet.set_wif(bitcoin_key)
                except Exception as e:
                    print(f"Error setting WIF for {name}: {e}")
                    sys.exit(1)
                self.actors_wallets[name] = wallet

                token_wallet = TokenWallet()
                token_wallet.set_key(token_key, token_key_curve)
                self.actors_token_wallets[name] = token_wallet

                eth_wallet = EthereumWallet(self.ethereum_service.web3, eth_key)
                print(f"Setting up Ethereum wallet for {name}")
                self.actors_eth_wallets[name] = eth_wallet

        except KeyError as e:
            print(f"Configuration error: Missing key {e}")
            sys.exit(1)
        except TypeError:
            print("Configuration error: 'config' is not properly set or 'actor' is not a list")
            sys.exit(1)
        except ValueError as e:
            print(f"Configuration error: {e}")
            sys.exit(1)

    def set_config(self, config: ConfigType):
        """ Given the configuration, configure this service
        """

        # Financing service
        self.finance_service.set_config(config)

        # BSV
        self.blockchain_network = config["blockchain"]["network"]
        self.blockchain_interface = interface_factory.set_config(config["blockchain"])

        # Ethereum
        self.ethereum_service.set_config(config)

        self.set_actors(config)
        self.networks = config["commitment_service"]["networks"]
        self.commitment_store.set_config(config)
        self.commitment_store.load()

        token_store.set_config(config)
        token_store.load()

    def test_financing_service(self) -> bool:
        """ Return True if financing service working
        """
        try:
            self.finance_service.get_status()
        except FinancingServiceException as e:
            print(f"exception {e}")
            return False
        else:
            return True

    def _broadcast_tx(self, tx: Tx) -> None | Txid:
        """ Given a tx broadcast it and if successful return the Txid
        """
        print(f'_broadcast_tx -> {tx.serialize().hex()}')
        result = self.blockchain_interface.broadcast_tx(tx.serialize().hex())
        if result is None:
            return None
        else:
            # the result error code is not being checked. I'll leave this unhelpful
            # comment here for now
            return Txid(tx.id())

    def get_funds(self, fee_estimate: int, locking_script: str) -> None | Tuple[TxIn, Tx]:
        """ Get a funding tx that can be spent by the provided locking_script
        """
        result = self.finance_service.get_funds(fee_estimate, locking_script)
        if result is None:
            return None
        if result['status'] != "Success":
            return None
        # Get the Oupoint
        outpoints = result['outpoints'][0]
        vin = TxIn(prev_tx=outpoints['hash'], prev_index=outpoints['index'])
        # Get the Tx
        tx_as_hexstr = result['tx']
        tx = hexstr_to_tx(tx_as_hexstr)
        assert isinstance(tx, Tx)
        return (vin, tx)

    def _get_tx(self, txid: Txid) -> None | Tx:
        """ Given the txid return the transaction
        """
        source_tx_hex = self.blockchain_interface.get_raw_transaction(txid)
        if source_tx_hex is None:
            print(f"unable to find txid = {txid}")
            return None
        # Do some checks of the source tx
        assert isinstance(source_tx_hex, str)
        return hexstr_to_tx(source_tx_hex)

    def get_status(self) -> Dict[str, Any]:
        """ Return the service status
        """
        # eth wallets are connected
        return {
            "status": "running",
            "finance_get_balance": self.finance_service.get_balance(),
            "actors": list(self.actors_wallets.keys()),
            "networks": self.networks,
            "ethereum_connected": self.ethereum_service.get_status(),
        }

    def is_known_actor(self, name: str) -> bool:
        """ Return true if actor is known
        """
        return name in self.actors_wallets

    def is_known_network(self, network: str) -> bool:
        """ Return true if network is known
        """
        return network in self.networks

    def is_known_cpid(self, cpid: str) -> bool:
        """ Return true if this is a know CPID
        """
        return self.commitment_store.is_known_cpid(cpid)

    def get_commitment_meta_by_cpid(self, cpid: str) -> None | CommitmentPacketMetadata:
        """ Given CPID return associated Commitment Packet and Metadata
        """
        return self.commitment_store.get_metadata_by_cpid(cpid)

    def get_commitments_by_actor(self, actor: str) -> List[Tuple[Cpid, CommitmentPacket]]:
        """ Return all Commitments made by this actor
        """
        assert self.is_known_actor(actor)
        return self.commitment_store.get_commitments_by_actor(actor)

    def get_transfers_by_actor(self, actor: str) -> List[Cpid]:
        """ Get Commitment Transfers of this actor's Commitments
        """
        assert self.is_known_actor(actor)
        return self.commitment_store.get_transfers_by_actor(actor)

    def get_commitment_tx_by_cpid(self, cpid: str) -> None | str:
        """ Given the cpid return the transaction ownership_tx in the Commitment
        """
        assert self.is_known_cpid(cpid)
        cp = self.commitment_store.get_metadata_by_cpid(cpid)
        if cp is None:
            return None
        assert isinstance(cp, CommitmentPacketMetadata)
        tx = hexstr_to_tx(cp.ownership_tx)
        if tx is None:
            return None

        assert isinstance(tx, Tx)
        link = f"https://test.whatsonchain.com/tx/{tx.id()}"
        return link

    def public_key_to_owner(self, public_key: str) -> None | str:
        for name, wallet in self.actors_token_wallets.items():
            if wallet.get_token_public_key() == public_key:
                return name
        return None

    def cp_meta_to_status(self, cpid: str, cp: CommitmentPacketMetadata) -> Dict[str, Any]:
        retval = cp.model_dump()
        del retval["ownership_tx"]
        del retval["spending_tx"]
        if retval["type"] == "Issuance":
            # Issuance has no previous packet
            del retval["commitment_packet"]["previous_packet"]

        # Show tx
        network = cp.commitment_packet.blockchain_id
        match network:
            case "BSV":
                txid_and_index = cp.commitment_packet.get_blockchain_txid_and_index()
                if txid_and_index is not None:
                    (txid, index) = txid_and_index
                    retval["commitment_packet"]["blockchain_outpoint_link"] = f"https://test.whatsonchain.com/tx/{txid}"
            case _:
                raise NotImplementedError(f"Unknown network '{network}'")
        # Lookup public key
        owner = self.public_key_to_owner(retval["commitment_packet"]["public_key"])
        if owner is not None:
            retval["commitment_packet"]["public_key_owner"] = owner
        del retval["commitment_packet"]["public_key"]

        # Check signature
        if retval["commitment_packet"]["signature"] is not None:
            retval["commitment_packet"]["signature_valid"] = self.is_signature_valid(cpid)
            del retval["commitment_packet"]["signature"]
        del retval["commitment_packet"]["signature_scheme"]
        return retval

    def get_commitment_status(self, cpid: str) -> None | List[Dict[str, Any]]:
        """ Given the cpid return the Commitment status as a dictionary of information
        """
        retval: List[Dict[str, Any]] = []
        assert self.is_known_cpid(cpid)
        while cpid is not None:
            cp = self.commitment_store.get_metadata_by_cpid(cpid)
            if cp is None:
                return None
            assert isinstance(cp, CommitmentPacketMetadata)
            status = self.cp_meta_to_status(cpid, cp)
            retval.append(status)
            if cp.commitment_packet.previous_packet is not None:
                cpid = cp.commitment_packet.previous_packet
            else:
                break
        return retval

    def is_commitment_unique(self, asset_id: str, asset_data: str, network: str) -> bool:
        return self.commitment_store.is_commitment_unique(asset_id, asset_data, network)

    def commitment_packets_owned_by_actor(self, actor: str) -> None | List[Tuple[Cpid, CommitmentPacket]]:
        # check the commitment store by actor for commitments
        # the public key on the packet must match & it must not have a spending tx
        # final check .. token store .. the id should be assigned to this actor & the CPID must match
        return_list: List[Tuple[Cpid, CommitmentPacket]] = []
        commitment_packets: List[Tuple[Cpid, CommitmentPacket]] = self.commitment_store.get_commitments_by_actor_without_spending_tx(actor)
        tokens_by_actor = token_store.token_list_by_actor(actor)
        for id, packet in commitment_packets:
            packet_list = [(Cpid(obj.cpid), packet) for obj in tokens_by_actor if obj.cpid == id]
            if len(packet_list) > 0:
                return_list.extend(packet_list)
        return return_list

    def get_commitment_tx_hash(self, cpid: str) -> Optional[str]:
        """Given a CPID, return the commitment tx hash (spending_tx)"""
        # given the cpid .. get the previous cpid
        cp_metadata: Optional[CommitmentPacketMetadata] = self.commitment_store.get_metadata_by_cpid(cpid)
        if cp_metadata is None:
            return None

        # Initialize cp_prev_metadata
        cp_prev_metadata: Optional[CommitmentPacketMetadata] = None

        # get the meta-data for the previous packet.
        if cp_metadata.commitment_packet.previous_packet is None:
            # the issuing case
            cp_prev_metadata = cp_metadata
        else:
            cp_prev_metadata = self.commitment_store.get_metadata_by_cpid(cp_metadata.commitment_packet.previous_packet)
            if cp_prev_metadata is None:
                return None

        # get the previous commitment metadata
        if cp_prev_metadata.spending_tx is None:
            return None

        if cp_prev_metadata.commitment_packet.blockchain_id == "ETH":
            return cp_prev_metadata.spending_tx
        elif cp_prev_metadata.commitment_packet.blockchain_id == "BSV":
            return hexstr_to_txid(cp_prev_metadata.spending_tx)
        else:
            return None

    def bsv_create_ownership_tx(self, locking_script_as_hex: str) -> None | Tuple[TxIn, Tx]:
        """ Given a locking script return a BSV UTXO
        """
        UTXO_VALUE = 100
        results = self.finance_service.get_funds(UTXO_VALUE, locking_script_as_hex)
        if results is None:
            print("unable to get funds")
            return None
        assert isinstance(results, dict)
        assert results['status'] == 'Success'
        first_outpoint = results['outpoints'][0]
        outpoint = TxIn(prev_tx=first_outpoint['hash'], prev_index=first_outpoint['index'])
        tx = hexstr_to_tx(results['tx'])
        assert isinstance(tx, Tx)
        return (outpoint, tx)

    def bsv_spend_ownership_tx(self, wallet: Wallet, outpoint: TxIn, ownership_tx: None | Tx, cpid: Cpid) -> None | Tx:
        """ Spend the previously created BSV UTXO
        """
        if ownership_tx is None:
            # then request tx
            ownership_tx = self._get_tx(Txid(outpoint.prev_tx))
            if ownership_tx is None:
                print("Unable to find utxo")
                return None

        op_return_script: Script = Script.parse_string("OP_0 OP_RETURN")
        op_return_script.append_pushdata(bytes.fromhex(cpid))
        tx_out = TxOut(amount=0, script_pubkey=op_return_script)
        spending_tx = Tx(version=1, tx_ins=[outpoint], tx_outs=[tx_out])
        # This transaction only has 1 input, hence the magic 0 for the index to sign
        signed_spending_tx = wallet.sign_tx_with_input(0, ownership_tx, spending_tx)
        if signed_spending_tx is None:
            print("Sign spending tx failed")
            return None
        if self._broadcast_tx(signed_spending_tx) is not None:
            return signed_spending_tx
        else:
            print("Unable to broadcast tx")
            return None

    def create_ownership_tx(self, actor: str, network: str) -> None | Tuple[TxIn, Tx]:
        """ Create UTXO based on actor info and network
        """
        match network:
            case 'BSV':
                actors_wallet = self.actors_wallets[actor]
                return self.bsv_create_ownership_tx(actors_wallet.get_locking_script_as_hex())
            case 'ETH':
                eth_actors_wallet = self.actors_eth_wallets[actor]
                print("Calling Ethereum service to create UTXO")
                tx_hash = self.ethereum_service.create_ownership_tx(eth_actors_wallet)
                print(f"tx_hash = {tx_hash}")
                # expects a tuple, ethereum only returns the tx_hash
                return tx_hash, tx_hash
            case _: raise NotImplementedError(f"Unknown network '{network}'")

    def spend_ownership_tx(self, actor: str, network: str, outpoint: TxIn, ownership_tx: None | Tx, cpid: Cpid) -> None | Tx:
        actors_wallet = self.actors_wallets[actor]
        return self.bsv_spend_ownership_tx(actors_wallet, outpoint, ownership_tx, cpid)

    def spend_ownership_tx_eth(self, actor: str, tx_hash: str, cpid: Cpid) -> None | str:
        actors_wallet = self.actors_eth_wallets[actor]
        assert actors_wallet is not None
        tx_hash = self.ethereum_service.spend_ownership_tx(tx_hash, actors_wallet, cpid)
        return tx_hash

    def sign_commitment_packet(self, actor: str, cp: CommitmentPacket) -> CommitmentPacket:
        assert self.is_known_actor(actor)
        token_wallet = self.actors_token_wallets[actor]
        cp_digest: bytes = cp.packet_digest()
        cp_digest_sig: bytes = token_wallet.sign_commitment_packet_digest(cp_digest, hashlib.sha256)
        cp.signature = cp_digest_sig.hex()
        return cp

    def create_issuance_commitment(self, actor: str, asset_id: str, asset_data: str, network: str) -> None | Tuple[Cpid, CommitmentPacket]:
        """ Create Issuance Commitment Packet
        """
        assert self.is_known_actor(actor)
        assert self.is_known_network(network)
        # check the token_id (denoted by asset_data right now) is in the token_store

        assert (token_store.check_token_id(asset_data))

        # Create utxo
        result = self.create_ownership_tx(actor, network)
        if result is None:
            # Return error
            return None
        (vin, utxo_tx) = result

        match network:
            case 'BSV':
                # Create commitment packet
                cp = CommitmentPacket(
                    asset_id=asset_id,
                    data=asset_data,
                    previous_packet=None,
                    blockchain_outpoint=vin.as_outpoint(),
                    blockchain_id=network,
                    signature=None,
                    signature_scheme=None,
                    public_key=None,
                )  # type: ignore[call-arg]

            case 'ETH':
                # Create commitment packet
                cp = CommitmentPacket(
                    asset_id=asset_id,
                    data=asset_data,
                    previous_packet=None,
                    blockchain_outpoint=vin,
                    blockchain_id=network,
                    signature=None,
                    signature_scheme=None,
                    public_key=None,
                )  # type: ignore[call-arg]

        # The current owner addes the sig scheme & their public key
        assert self.is_known_actor(actor)
        token_wallet = self.actors_token_wallets[actor]
        cp.signature_scheme = token_wallet.get_signature_scheme()
        cp.public_key = token_wallet.get_token_public_key()
        # Sign commitment packet
        cp = self.sign_commitment_packet(actor, cp)
        # Store commitment packet
        cpid = cp.get_cpid()
        # assign token to actor
        if not token_store.assign_to_actor(actor, asset_data, cpid):
            print(f'Problem with assert ID -> {asset_data} in the token store')

        match network:
            case 'BSV':

                cp_meta = CommitmentPacketMetadata(
                    owner=actor,
                    type=CommitmentType.Issuance,
                    state=CommitmentStatus.Created,
                    ownership_tx=tx_to_hexstr(utxo_tx),
                    spending_tx=None,
                    commitment_packet_id=cpid,
                    commitment_packet=cp
                )
            case 'ETH':
                cp_meta = CommitmentPacketMetadata(
                    owner=actor,
                    type=CommitmentType.Issuance,
                    state=CommitmentStatus.Created,
                    ownership_tx=utxo_tx,
                    spending_tx=None,
                    commitment_packet_id=cpid,
                    commitment_packet=cp
                )

        self.commitment_store.add_commitment(cp_meta)

        # Return commitment packet
        return (cpid, cp)

    def is_signature_valid(self, cpid: str) -> bool:
        cp_meta = self.commitment_store.get_metadata_by_cpid(cpid)
        if cp_meta is None:
            return False
        cp = self.commitment_store.get_commitment_by_cpid(cpid)
        if cp is None:
            return False
        prev_cp = self.commitment_store.get_commitment_by_cpid(cp.previous_packet)
        pubkey_to_use: Optional[str] = None
        if prev_cp is None:
            pubkey_to_use = cp.public_key
        else:
            pubkey_to_use = prev_cp.public_key

        assert pubkey_to_use is not None

        message: bytes = cp.packet_digest()
        c: ecdsa.curves.Curve = ecdsa.curves.curve_by_name(cp.signature_scheme)
        if not verify_signature(message, pubkey_to_use, bytes.fromhex(cp.signature), c, hashlib.sha256):
            print(f'Failing to verify signature? for cpid -> {cpid}')
            return False

        return True

    def can_transfer(self, cpid: str, actor: str, is_owner: bool) -> bool:
        if self.commitment_store.can_transfer(cpid, actor, is_owner):

            return self.is_signature_valid(cpid)
        return False

    def create_transfer_template(self, cpid: str, actor: str, network: str) -> None | Tuple[Cpid, CommitmentPacket]:
        """ Create Commitment Packet Template
        """
        assert self.is_known_cpid(cpid)
        assert self.is_known_actor(actor)
        assert self.is_known_network(network)

        # <TODO> - we need to check directly on the blockchain if the outpoint has been spent
        # for ethereum, use ethereum_service.txSpentStatus()
        # Get the previous Commitment Packet & metadata
        orignal_cp_meta = self.commitment_store.get_metadata_by_cpid(cpid)
        if orignal_cp_meta is None:
            print(f"Unable to find commitment packet {cpid}")
            return None

        assert self.can_transfer(cpid, actor, is_owner=False)

        # check the owner of the original cp also has ownership in the token store
        if not token_store.check_token_id_actor(orignal_cp_meta.owner, orignal_cp_meta.commitment_packet.data):
            print('Issue with orignal ownersip {orignal_cp_meta.owner} on token_id {orignal_cp_meta.commitment_packet.data}')
        # Create transfer template
        # Create utxo
        result = self.create_ownership_tx(actor, network)
        if result is None:
            # Return error
            return None
        (vin, utxo_tx) = result

        # Create commitment packet

        # get the token wallet of the actor creating the transfer template
        token_wallet = self.actors_token_wallets[actor]
        match network:
            case 'BSV':
                cp = CommitmentPacket(
                    asset_id=orignal_cp_meta.commitment_packet.asset_id,
                    data=orignal_cp_meta.commitment_packet.data,
                    previous_packet=orignal_cp_meta.commitment_packet_id,
                    blockchain_outpoint=vin.as_outpoint(),
                    blockchain_id=network,
                    signature_scheme=token_wallet.get_signature_scheme(),
                    public_key=token_wallet.get_token_public_key(),
                    signature=None,
                )  # type: ignore[call-arg]
            case 'ETH':
                cp = CommitmentPacket(
                    asset_id=orignal_cp_meta.commitment_packet.asset_id,
                    data=orignal_cp_meta.commitment_packet.data,
                    previous_packet=orignal_cp_meta.commitment_packet_id,
                    blockchain_outpoint=vin,
                    blockchain_id=network,
                    signature_scheme=token_wallet.get_signature_scheme(),
                    public_key=token_wallet.get_token_public_key(),
                    signature=None,
                )  # type: ignore[call-arg]

        # Store commitment packet
        cpid = cp.get_cpid()

        match network:
            case 'BSV':

                cp_meta = CommitmentPacketMetadata(
                    owner=actor,
                    type=CommitmentType.Transfer,
                    state=CommitmentStatus.Created,
                    ownership_tx=tx_to_hexstr(utxo_tx),
                    spending_tx=None,
                    commitment_packet_id=cpid,
                    commitment_packet=cp,
                )
            case 'ETH':

                cp_meta = CommitmentPacketMetadata(
                    owner=actor,
                    type=CommitmentType.Transfer,
                    state=CommitmentStatus.Created,
                    ownership_tx=utxo_tx,
                    spending_tx=None,
                    commitment_packet_id=cpid,
                    commitment_packet=cp,
                )

        self.commitment_store.add_commitment(cp_meta)

        # move the token id to the new owner in the token_store
        # Return commitment packet
        return (cpid, cp)

    def can_complete_transfer(self, cpid: str, actor: str) -> bool:
        return self.commitment_store.can_complete_transfer(cpid, actor)

    def complete_transfer(self, cpid: str, actor: str) -> None | Tuple[Cpid, CommitmentPacket]:
        """ Complete Commitment Packet Template
        """
        assert self.is_known_cpid(cpid)
        assert self.is_known_actor(actor)
        assert self.can_complete_transfer(cpid, actor)

        # Check the signature on the template is correct
        # Owner to complete template
        transfer_cp_meta = self.commitment_store.get_metadata_by_cpid(cpid)
        if transfer_cp_meta is None:
            print(f"Unable to find cpid {cpid}")
            return None
        # TODO: what fields need to be updated?

        # Update the orignal commitment to show that it is now transferred
        previous_cp_meta = self.commitment_store.get_metadata_by_cpid(transfer_cp_meta.commitment_packet.previous_packet)
        if previous_cp_meta is None:
            print(f"Unable to find cpid {cpid} of previous packet")
            return None
        if previous_cp_meta.state != CommitmentStatus.Created:
            print(f"Previous CP in state {previous_cp_meta.state} ")
            return None

        # Create a spending tx
        network = previous_cp_meta.commitment_packet.blockchain_id
        outpoint = previous_cp_meta.commitment_packet.blockchain_outpoint
        assert outpoint is not None

        if network == "BSV":
            outpoint = hexstr_to_txin(outpoint)
            ownership_tx = hexstr_to_tx(previous_cp_meta.ownership_tx)
            spending_tx = self.spend_ownership_tx(actor, network, outpoint, ownership_tx, transfer_cp_meta.commitment_packet_id)
        elif network == "ETH":
            spending_tx = self.spend_ownership_tx_eth(actor, outpoint, transfer_cp_meta.commitment_packet_id)
        else:
            print(f"Unknown network {network}")
            return None
        if spending_tx is None:
            print(f"Unable to spend outpoint {outpoint} on {network}")
            return None

        # Sign commitment packet
        transfer_cp_meta.commitment_packet = self.sign_commitment_packet(actor, transfer_cp_meta.commitment_packet)
        self.commitment_store.update_commitment(transfer_cp_meta)
        # Transfer token ownership
        if not token_store.assign_to_new_actor(previous_cp_meta.owner, transfer_cp_meta.owner, transfer_cp_meta.commitment_packet.data, transfer_cp_meta.commitment_packet.get_cpid()):
            print(f'Could not transfer token store ownership from {previous_cp_meta.owner} to {transfer_cp_meta.owner} with token_id -> {transfer_cp_meta.commitment_packet.data} and CPID -> {transfer_cp_meta.commitment_packet.get_cpid()}')
        previous_cp_meta.state = CommitmentStatus.Transferred
        if previous_cp_meta.commitment_packet.blockchain_id == "BSV":
            previous_cp_meta.spending_tx = tx_to_hexstr(spending_tx) if spending_tx is not None else None
        elif previous_cp_meta.commitment_packet.blockchain_id == "ETH":
            previous_cp_meta.spending_tx = spending_tx if spending_tx is not None else None
        else:
            print(f"Unknown network { previous_cp_meta.commitment_packet.blockchain_id}")
            return None
        self.commitment_store.update_commitment(previous_cp_meta)

        return (Cpid(cpid), transfer_cp_meta.commitment_packet)


commitment_service = CommitmentService()
