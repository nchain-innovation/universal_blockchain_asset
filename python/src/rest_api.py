import os

from fastapi import FastAPI, Response, status, HTTPException, Form, UploadFile, File
from fastapi.responses import JSONResponse
from starlette.responses import FileResponse

from typing import Any, Dict, Optional
from pydantic import BaseModel

from service.commitment_service import commitment_service
from service.token_description import token_store
from service.file_storage import FileStorage



CONFIG_FILE = "../data/uba-server.toml" if os.environ.get("APP_ENV") == "docker" else "../../data/uba-server.toml"


tags_metadata = [
    {
        "name": "UBA Token System REST API",
        "description": "UBA Token System REST API",
    },
]


app = FastAPI(
    title="UBA Token System REST API",
    description="UBA Token System REST API",
    openapi_tags=tags_metadata,
)

# Initialise FileStorage class with allowed extensions
file_storage = FileStorage(allowed_extensions={"png", "jpg", "jpeg"})


@app.get("/status", tags=["Status"])
def get_status() -> Dict[str, Any]:
    """ Status - returns the current service status and number of certificates held. """
    return commitment_service.get_status()


@app.get("/commitment", tags=["Tokens"])
def get_commitment_metadata_by_cpid(cpid: str) -> Response:
    """ Get UBA Metadata (and UBA) associated with this CPID
    """
    commitment = commitment_service.get_commitment_meta_by_cpid(cpid)
    if commitment is None:
        return JSONResponse(content={"message": "Unable to find any UBA Packets"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        serialisable_commitment = commitment.model_dump()
        return JSONResponse(content={"message": serialisable_commitment}, status_code=status.HTTP_200_OK)


@app.get("/commitment/history", tags=["Tokens"])
def get_commitment_history_by_cpid(cpid: str) -> Response:
    """ Get Commitment History associated with this CPID
    """
    if not commitment_service.is_known_cpid(cpid):
        return JSONResponse(content={"message": "Unable to find the Commitment Packet"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        history = commitment_service.get_commitment_history_by_cpid(cpid)

        if history == []:
            return JSONResponse(content={"message": "Unable to find any Commitment Packets"}, status_code=status.HTTP_400_BAD_REQUEST)
        else:
            serialisable_history = [{c[0]: c[1].dict()} for c in history]
            return JSONResponse(content={"message": serialisable_history}, status_code=status.HTTP_200_OK)


@app.get("/commitment/tx", tags=["Tokens"])
def get_commitment_transaction(cpid: str) -> Response:
    """ Given the cpid return the transaction ownership_tx in the Commitment
    """
    if not commitment_service.is_known_cpid(cpid):
        return JSONResponse(content={"message": "Unable to find any UBA Packeta"}, status_code=status.HTTP_400_BAD_REQUEST)
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
    return JSONResponse(content={"message": "Not implemented"}, status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get("/commitments", tags=["Tokens"])
def get_commitments_by_actor(actor: str) -> Response:
    """ Get UBA associated with this actor
    """
    if not commitment_service.is_known_actor(actor):
        return JSONResponse(content={"message": f"Unknown actor {actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    commitments = commitment_service.get_commitments_by_actor(actor)
    if commitments == []:
        return JSONResponse(content={"message": "Unable to find any UBAs"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        serialisable_commitments = [
            {c[0]: c[1].model_dump() if hasattr(c[1], 'model_dump') else c[1]} for c in commitments
        ]
        return JSONResponse(content={"message": serialisable_commitments}, status_code=status.HTTP_200_OK)


@app.get("/commitments/transfers", tags=["Tokens"])
def get_transfers_by_actor(actor: str) -> Response:
    """ Get UBA Transfers of this actor's UBAs
    """
    if not commitment_service.is_known_actor(actor):
        return JSONResponse(content={"message": f"Unknown actor {actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    commitments = commitment_service.get_transfers_by_actor(actor)
    if commitments == []:
        return JSONResponse(content={"message": "Unable to find any UBAs"}, status_code=status.HTTP_400_BAD_REQUEST)
    else:
        serialisable_commitments = [
            {c[0]: c[1].model_dump() if hasattr(c[1], 'model_dump') else c[1]} for c in commitments
        ]
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
    # print(token_list_str)
    return JSONResponse(content={"message": {'tokens': token_list_str}}, status_code=status.HTTP_200_OK)


@app.get("/commitment_detail_by_actor", tags=["Tokens"])
def commitment_detail_by_actor(actor: str) -> Response:
    """ Returns a list of UBA packets owned by actor that are available
        for purchase by others
    """
    if not commitment_service.is_known_actor(actor):
        return JSONResponse(content={"message": f"Unknown actor {actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    commit_packet_list = commitment_service.commitment_packets_owned_by_actor(actor)
    if commit_packet_list is None:
        return JSONResponse(content={"message": "No commitment packets found"}, status_code=status.HTTP_400_BAD_REQUEST)

    serialisable_commitment_list = []
    for c in commit_packet_list:
        key = c[0]
        value = c[1]
        if hasattr(value, 'model_dump'):
            serialisable_commitment_list.append({key: value.model_dump()})
        else:
            serialisable_commitment_list.append({key: value.__dict__})

    return JSONResponse(content={"message": serialisable_commitment_list}, status_code=status.HTTP_200_OK)


@app.get("/commitment_transaction_hash", tags=["Tokens"])
def commitment_transaction_hash(cpid: str) -> Response:
    """ Returns the UBA transaction hash for the parent of a given CPID
    """
    if not commitment_service.is_known_cpid(cpid):
        return JSONResponse(content={"message": "Unable to find any UBA Packets"}, status_code=status.HTTP_400_BAD_REQUEST)

    tx_hash: Optional[str] = commitment_service.get_commitment_tx_hash(cpid)
    if tx_hash is None:
        return JSONResponse(content={"message": f"Unknown cpid {cpid}"}, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content={"message": {'Commitment_TX_Hash': tx_hash}}, status_code=status.HTTP_200_OK)


class IssuanceParameters(BaseModel):
    """ The parameters required to create a UBA
    """
    actor: str
    asset_id: str
    asset_data: str
    network: str


@app.post("/asset/create", status_code=201, tags=["Assets"])
async def asset_create(
    username: str = Form(...),  # Get username from form
    file: UploadFile = File(...)  # Get the file upload
) -> Dict[str, str]:
    """Upload an image, validate, and save it using the FileStorage class."""

    try:
        # Read the file content asynchonously
        file_content = await file.read()

        # Delegate the file saving and validation to FileStorage
        asset_id = file_storage.save_file(file_content, file.filename, username)

        response = {
            "username": username,
            "asset_id": asset_id,
            "status": "File uploaded and saved successfully"
        }

        return response
    except ValueError as e:
        # If the file type is not allowed, return a 400 error
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Handle other server-side errors
        raise HTTPException(status_code=500, detail="Error saving file") from e



@app.get("/asset/retrieve/{asset_id}/{username}", tags=["Assets"])
def asset_retrieve(asset_id: str, username: str) -> FileResponse:
    """Retrieve file data by UUID and username."""
    try:
        file_data = file_storage.get_file_data(unique_reference=asset_id, username=username)
        file_path = file_data["file_path"]
        filename = file_data["filename"]
        return FileResponse(file_path, filename=filename)
    except ValueError as e:
        print(f"Error retrieving file: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/commitments/issuance", tags=["Tokens"])
def create_issuance_commitment(commit_param: IssuanceParameters) -> Response:
    """ Create an Issuance UBA Packet
    """
    if not commitment_service.is_known_actor(commit_param.actor):
        return JSONResponse(content={"message": f"Unknown actor {commit_param.actor}"}, status_code=status.HTTP_400_BAD_REQUEST)

    if not commitment_service.is_known_network(commit_param.network):
        return JSONResponse(content={"message": f"Unknown network {commit_param.network}"}, status_code=status.HTTP_400_BAD_REQUEST)

    if not commitment_service.is_commitment_unique(commit_param.asset_id, commit_param.asset_data, commit_param.network):
        return JSONResponse(content={"message": "This UBA already exists"}, status_code=status.HTTP_400_BAD_REQUEST)

    cpid_commitment = commitment_service.create_issuance_commitment(
        commit_param.actor, commit_param.asset_id, commit_param.asset_data, commit_param.network)
    if cpid_commitment is not None:
        (cpid, commitment) = cpid_commitment
        serialised_commitment = commitment.model_dump()
        return JSONResponse(content={"message": {cpid: serialised_commitment}}, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content={"message": "Unable to create UBA packet"}, status_code=status.HTTP_400_BAD_REQUEST)


class TemplateParameters(BaseModel):
    """ The parameters required to create a UBA packet template
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
        return JSONResponse(content={"message": "Unable to Transfer UBA Packet"}, status_code=status.HTTP_400_BAD_REQUEST)

    try:
        cpid_commitment = commitment_service.create_transfer_template(
            commit_transfer_param.cpid, commit_transfer_param.actor, commit_transfer_param.network)
        if cpid_commitment is not None:
            (cpid, commitment) = cpid_commitment
            serialised_commitment = commitment.model_dump()
            return JSONResponse(content={"message": {cpid: serialised_commitment}}, status_code=status.HTTP_200_OK)
        else:
            return JSONResponse(content={"message": "Unable to create a transfer UBA packet template"}, status_code=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return JSONResponse(content={"message": f"Error: {e}"}, status_code=status.HTTP_400_BAD_REQUEST)


class CompleteTransferParameters(BaseModel):
    """ The parameters required to create a UBA packet template
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
        return JSONResponse(content={"message": "Unable to Complete Transfer UBA Packet"}, status_code=status.HTTP_400_BAD_REQUEST)

    cpid_commitment = commitment_service.complete_transfer(commit_transfer_param.cpid, commit_transfer_param.actor)
    if cpid_commitment is not None:
        (cpid, commitment) = cpid_commitment
        serialised_commitment = commitment.model_dump()
        return JSONResponse(content={"message": {cpid: serialised_commitment}}, status_code=status.HTTP_200_OK)
    else:
        return JSONResponse(content={"message": "Unable to complete a transfer"}, status_code=status.HTTP_400_BAD_REQUEST)
