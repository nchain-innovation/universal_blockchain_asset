import os
import ecdsa

from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse

from typing import Any, Dict
from pydantic import BaseModel

from service.commitment_service import commitment_service
from service.token_description import token_store

#from tx_engine.engine.format import bytes_to_wif

CONFIG_FILE = "../data/commitment-server.toml" if os.environ.get("APP_ENV") == "docker" else "../../data/commitment-server.toml"


# Restful API guidence
# https://confluence.stressedsharks.com/display/PCREC/How+To%3A+Build+RESTful+APIs#HowTo:BuildRESTfulAPIs-HTTPmethods

tags_metadata = [
    {
        "name": "Commitment Token System REST API",
        "description": "Commitment Token System REST API",
    },
]


app = FastAPI(
    title="Commitment Token System REST API",
    description="Commitment Token System REST API",
    openapi_tags=tags_metadata,
)


@app.get("/status", tags=["Status"])
def get_status() -> Dict[str, Any]:
    """ Status - returns the current service status and number of certificates held. """
    return commitment_service.get_status()


@app.get("/commitment", tags=["Tokens"])
def get_commitment_metadata_by_cpid(cpid: str) -> Response:
    """ Get Commitment Metadata (and Commitment) associated with this CPID
    """
    commitment = commitment_service.get_commitment_meta_by_cpid(cpid)
    if commitment is None:
        return JSONResponse(content={"message": "Unable to find any Commitment Packet"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        serialisable_commitment = commitment.dict()
        return JSONResponse(content={"message": serialisable_commitment}, status_code=status.HTTP_200_OK)


@app.get("/commitment/tx", tags=["Tokens"])
def get_commitment_transaction(cpid: str) -> Response:
    """ Given the cpid return the transaction ownership_tx in the Commitment
    """
    if not commitment_service.is_known_cpid(cpid):
        return JSONResponse(content={"message": "Unable to find any Commitment Packet"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        result = commitment_service.get_commitment_tx_by_cpid(cpid)
        if result is None:
            return JSONResponse(content={"message": "Unable to find transaction"}, status_code=status.HTTP_400_BAD_REQUEST)
        else:
            return JSONResponse(content={"message": result}, status_code=status.HTTP_200_OK)


@app.get("/commitment/status", tags=["Tokens"])
def get_commitment_status(cpid: str) -> Response:
    """ Given the cpid return the Commitment status
    """
    if not commitment_service.is_known_cpid(cpid):
        return JSONResponse(content={"message": "Unable to find any Commitment Packet"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        result = commitment_service.get_commitment_status(cpid)
        if result is None:
            return JSONResponse(content={"message": "Unable to find transaction"}, status_code=status.HTTP_400_BAD_REQUEST)
        else:
            return JSONResponse(content={"message": result}, status_code=status.HTTP_200_OK)


@app.get("/commitments", tags=["Tokens"])
def get_commitments_by_actor(actor: str) -> Response:
    """ Get Commitments associated with this actor
    """
    if not commitment_service.is_known_actor(actor):
        return JSONResponse(content={"message": f"Unknown actor {actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    commitments = commitment_service.get_commitments_by_actor(actor)
    if commitments == []:
        return JSONResponse(content={"message": "Unable to find any Commitments"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        serialisable_commitments = [{c[0]: c[1].dict()} for c in commitments]
        return JSONResponse(content={"message": serialisable_commitments}, status_code=status.HTTP_200_OK)


@app.get("/commitments/transfers", tags=["Tokens"])
def get_transfers_by_actor(actor: str) -> Response:
    """ Get Commitment Transfers of this actor's Commitments
    """
    if not commitment_service.is_known_actor(actor):
        return JSONResponse(content={"message": f"Unknown actor {actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    commitments = commitment_service.get_transfers_by_actor(actor)
    if commitments == []:
        return JSONResponse(content={"message": "Unable to find any Commitments"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        serialisable_commitments = [{c[0]: c[1].dict()} for c in commitments]
        return JSONResponse(content={"message": serialisable_commitments}, status_code=status.HTTP_200_OK)


@app.get("/token_list", tags=["Tokens"])
def available_token_list() -> Response:
    """ Get a list of token descriptions and CIDs
    """
    return JSONResponse(content={"message": token_store.__repr__()})


@app.get("/token_to_actor", tags=["Tokens"])
def token_to_actor(actor: str, token_id: str, cpid: str) -> Response:
    """ Assigns a token to an actor
    """
    if not token_store.assign_to_actor(actor, token_id, cpid):
        return JSONResponse(content={"message": {"status": False}})
    else:
        return JSONResponse(content={"message": {"status": True}})


@app.get("/return_token_to_list", tags=["Tokens"])
def return_to_available_token_list(actor: str, token_id: str) -> Response:
    """ Assigns a token to an actor
    """
    if not token_store.return_to_pool(actor, token_id):
        return JSONResponse(content={"message": {"status": False}})
    else:
        return JSONResponse(content={"message": {"status": True}})


@app.get("/tokens_by_actor", tags=["Tokens"])
def tokens_by_actor(actor: str) -> Response:
    """ Returns a list of tokens owned by an actor
    """
    token_list_str: str = token_store.tokens_by_actor(actor)
    print(token_list_str)
    return JSONResponse(content={"message": {'tokens': token_list_str}}, status_code=status.HTTP_200_OK)


@app.get("/commitment_detail_by_actor", tags=["Tokens"])
def commitment_detail_by_actor(actor: str) -> Response:
    """ Returns a list of commitment packets owned by actor that are available
        for purcahse by others
    """
    if not commitment_service.is_known_actor(actor):
        return JSONResponse(content={"message": f"Unknown actor {actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    commit_packet_list = commitment_service.commitment_packets_owned_by_actor(actor)
    serialisable_commitment_list = [{c[0]: c[1].dict()} for c in commit_packet_list]
    return JSONResponse(content={"message": serialisable_commitment_list}, status_code=status.HTTP_200_OK)


@app.get("/commitment_transaction_hash", tags=["Tokens"])
def commitment_transaction_hash(cpid: str) -> Response:
    """ Returns the commitment transaction hash for the parent of a given CPID
    """
    if not commitment_service.is_known_cpid(cpid):
        return JSONResponse(content={"message": "Unable to find any Commitment Packet"}, status_code=status.HTTP_400_BAD_REQUEST)

    tx_hash: str = commitment_service.get_commitment_tx_hash(cpid)
    if tx_hash is None:
        return JSONResponse(content={"message": f"Unknown cpid {cpid}"}, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content={"message": {'Commitment_TX_Hash': tx_hash}}, status_code=status.HTTP_200_OK)


class IssuanceParameters(BaseModel):
    """ The parameters required to create a commitment
    """
    actor: str
    asset_id: str
    asset_data: str
    network: str


@app.post("/commitments/issuance", tags=["Tokens"])
def create_issuance_commitment(commit_param: IssuanceParameters) -> Response:
    """ Create an Issuance Commitment Packet
    """
    if not commitment_service.is_known_actor(commit_param.actor):
        return JSONResponse(content={"message": f"Unknown actor {commit_param.actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    if not commitment_service.is_known_network(commit_param.network):
        return JSONResponse(content={"message": f"Unknown network {commit_param.network}"}, status_code=status.HTTP_400_BAD_REQUEST)

    if not commitment_service.is_commitment_unique(commit_param.asset_id, commit_param.asset_data, commit_param.network):
        return JSONResponse(content={"message": "This commitment already exists"}, status_code=status.HTTP_400_BAD_REQUEST)

    cpid_commitment = commitment_service.create_issuance_commitment(
        commit_param.actor, commit_param.asset_id, commit_param.asset_data, commit_param.network)
    if cpid_commitment is not None:
        (cpid, commitment) = cpid_commitment
        serialised_commitment = commitment.dict()
        return JSONResponse(content={"message": {cpid: serialised_commitment}}, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content={"message": "Unable to create commitment packet"}, status_code=status.HTTP_400_BAD_REQUEST)


class TemplateParameters(BaseModel):
    """ The parameters required to create a commitment packet template
    """
    cpid: str
    actor: str
    network: str


@app.post("/commitments/template", tags=["Tokens"])
def create_transfer_template(commit_transfer_param: TemplateParameters) -> Response:
    """ Create Transfer Template
    """
    if not commitment_service.is_known_cpid(commit_transfer_param.cpid):
        return JSONResponse(content={"message": "Unknown cpid"}, status_code=status.HTTP_400_BAD_REQUEST)

    if not commitment_service.is_known_actor(commit_transfer_param.actor):
        return JSONResponse(content={"message": f"Unknown actor {commit_transfer_param.actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    if not commitment_service.is_known_network(commit_transfer_param.network):
        return JSONResponse(content={"message": f"Unknown network {commit_transfer_param.network}"}, status_code=status.HTTP_400_BAD_REQUEST)

    if not commitment_service.can_transfer(commit_transfer_param.cpid, commit_transfer_param.actor, is_owner=False):
        return JSONResponse(content={"message": "Unable to Transfer Commitment Packet"}, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        cpid_commitment = commitment_service.create_transfer_template(
            commit_transfer_param.cpid, commit_transfer_param.actor, commit_transfer_param.network)
        if cpid_commitment is not None:
            (cpid, commitment) = cpid_commitment
            serialised_commitment = commitment.dict()
            return JSONResponse(content={"message": {cpid: serialised_commitment}}, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content={"message": "Unable to create a transfer commitment packet template"}, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return JSONResponse(content={"message": f"Error: {e}"}, status_code=status.HTTP_400_BAD_REQUEST)


class CompleteTransferParameters(BaseModel):
    """ The parameters required to create a commitment packet template
    """
    cpid: str
    actor: str


@app.post("/commitments/complete", tags=["Tokens"])
def complete_transfer(commit_transfer_param: CompleteTransferParameters) -> Response:
    """ Complete Transfer
    """
    if not commitment_service.is_known_cpid(commit_transfer_param.cpid):
        return JSONResponse(content={"message": "Unknown cpid"}, status_code=status.HTTP_400_BAD_REQUEST)

    if not commitment_service.is_known_actor(commit_transfer_param.actor):
        return JSONResponse(content={"message": f"Unknown actor {commit_transfer_param.actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    if not commitment_service.can_complete_transfer(commit_transfer_param.cpid, commit_transfer_param.actor):
        return JSONResponse(content={"message": "Unable to Complete Transfer Commitment Packet"}, status_code=status.HTTP_400_BAD_REQUEST)

    cpid_commitment = commitment_service.complete_transfer(commit_transfer_param.cpid, commit_transfer_param.actor)
    if cpid_commitment is not None:
        (cpid, commitment) = cpid_commitment
        serialised_commitment = commitment.dict()
        return JSONResponse(content={"message": {cpid: serialised_commitment}}, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content={"message": "Unable to complete a transfer"}, status_code=status.HTTP_400_BAD_REQUEST)

'''
@app.get("/keys/generate_private_key", tags=["KeyManagement"])
def generate_private_key(curve_id: str) -> Response:
    """ Given a curve return a randomly generated private key in WIF format
    """
    req_curve: ecdsa.curves.Curve = ecdsa.curves.curve_by_name(curve_id)
    if req_curve is None:
        return JSONResponse(content={"message": f"Unknown curve id {curve_id}"}, status_code=status.HTTP_400_BAD_REQUEST)

    key: ecdsa.SigningKey = ecdsa.SigningKey.generate(curve=req_curve)
    key_wif: str = bytes_to_wif(key.to_string(), 'BSV_Testnet')
    return JSONResponse(content={"message": {'key': key_wif}}, status_code=status.HTTP_200_OK)
'''
