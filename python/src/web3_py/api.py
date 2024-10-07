from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
import toml

import os
import sys

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from ethereum.ethereum_service import EthereumService
from ethereum.ethereum_wallet import EthereumWallet

# =================================================================================================
# Start FastAPI app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================================================================================================
# Instantiate ethereum_interface as a singleton
eth_service = None
eth_wallet = None

# =================================================================================================
# Endpoints


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Ethereum Service API!"}


# on startup
@app.on_event("startup")
def startup():
    global eth_service
    global eth_wallet

    config_filename = './data/ethereum.toml'

    #  check the file exists
    if not os.path.exists(config_filename):
        raise ValueError(f"Configuration file not found: {config_filename}")

    # Load the configuration from the TOML file
    config = toml.load(config_filename)

    eth_service = EthereumService()
    eth_service.set_config(config)

    eth_wallet = EthereumWallet(eth_service.web3, config["ethereum"]["privateKey"])


# return status
@app.get("/status")
def status():
    if eth_service is None:  # Added check
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialised")
    return eth_service.get_status()


# Create the Ownership transaction
@app.post("/createOwnership")
def createOwnership():
    if eth_service is None:
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialised")

    if eth_wallet is None:
        raise HTTPException(status_code=500, detail="Ethereum wallet is not initialised")

    try:
        tx_hash = eth_service.create_ownership_tx(eth_wallet)
        return {"tx_hash": tx_hash}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Create the spend ownership transaction
@app.post("/spendOwnership")
def spendOwnership(txid: str, CPID: str):
    if eth_service is None:  # Added check
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialised")

    if eth_wallet is None:
        raise HTTPException(status_code=500, detail="Ethereum wallet is not initialised")

    try:
        tx_hash = eth_service.spend_ownership_tx(txid, eth_wallet, CPID)
        return {"tx_hash": tx_hash}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Check the unspent status of a transaction
@app.get("/txSpentStatus")
def txSpentStatus(tx_hash: str):
    if eth_service is None:  # Added check
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialised")

    try:
        status = eth_service.get_tx_spent_status(txid=tx_hash)
        return {"status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get the CPID of a txid
@app.get("/getCPID")
def getCPID(txid: str):
    if eth_service is None:
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialised")

    try:
        cpid = eth_service.get_cpid_from_txid(txid)
        return {"CPID": cpid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get the event and utxo from a txid
@app.get("/getEventAndUtxo")
def getEventAndUtxo(txid: str):
    if eth_service is None:
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialised")

    try:
        event, utxo = eth_service.get_event_and_utxo(txid)
        return {"event": event, "utxo": utxo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
