from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException
import toml
from eth_factory import ethereum_interface_factory, isERC20, isRawTransaction, isSmartContract
import os

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
eth = None

# =================================================================================================
# Endpoints


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Ethereum API!"}


# on startup
@app.on_event("startup")
def startup():
    global eth

    config_filename = './data/ethereum.toml'

    #  check the file exists
    if not os.path.exists(config_filename):
        raise ValueError(f"Configuration file not found: {config_filename}")

    # Load the configuration from the TOML file
    config = toml.load(config_filename)

    # Check that all required fields are present
    required_fields = ['ethNodeUrl', 'apiKey', 'privateKey', 'interface_type', 'gas', 'gasPrice']
    if not all(field in config['ethereum'] for field in required_fields):
        missing_fields = [field for field in required_fields if field not in config['ethereum']]
        raise ValueError(f"Missing required fields in configuration: {', '.join(missing_fields)}")

    # Extract the configuration values
    ethNodeUrl = config['ethereum']['ethNodeUrl']
    apiKey = config['ethereum']['apiKey']
    # account         = config['ethereum']['account'] - not used, as we derive the account from the private key
    privateKey = config['ethereum']['privateKey']
    interface_type = config['ethereum']['interface_type']
    gas = config['ethereum']['gas']
    gasPrice = config['ethereum']['gasPrice']

    # Extract the 'interface' part where the name is interface_type
    interface_config = None
    for interface in config['interface']:
        if interface['name'] == interface_type:
            interface_config = interface
            break

    if interface_config is None:
        raise ValueError(f"No {interface_type} interface found in configuration")

    eth = ethereum_interface_factory(interface_type, ethNodeUrl, apiKey, privateKey, gas, gasPrice, interface_config)


# return status
@app.get("/status")
def status():
    if eth is None:  # Added check
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialized")
    return eth.is_connected()


# Get the balance of the account in Ether
@app.get("/getBalance")
async def getBalance() -> float:
    if eth is None:  # Added check
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialized")
    try:
        balance = eth.check_balance()
        return balance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Create the Ownership transaction
@app.post("/createOwnership")
def createOwnership():
    if eth is None:  # Added check
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialized")

    if isERC20(eth):
        try:
            tx_hash, contract_addr = eth.create_ownership()
            return {"tx_hash": tx_hash, "contract_address": contract_addr}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif isRawTransaction(eth):
        try:
            tx_hash = eth.create_ownership()
            return {"tx_hash": tx_hash}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    elif isSmartContract(eth):
        try:
            tx_hash = eth.create_ownership()
            return {"tx_hash": tx_hash}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    else:
        raise HTTPException(status_code=500, detail="Interface is not ERC20 or RawTransaction")


# Create the spend ownership transaction
@app.post("/spendOwnership")
def spendOwnership(txid: str, CPID: str):
    if eth is None:  # Added check
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialized")

    try:
        tx_hash = eth.spend_ownership(txid, CPID)
        return {"tx_hash": tx_hash}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Check the unspent status of a transaction
@app.get("/txSpentStatus")
def txSpentStatus(tx_hash: str):
    if eth is None:  # Added check
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialized")

    try:
        status = eth.tx_spent_status(tx_hash=tx_hash)
        return {"status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get the CPID of a txid
@app.get("/getCPID")
def getCPID(txid: str):
    if eth is None:
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialized")

    try:
        cpid = eth.get_cpid(txid)
        return {"CPID": cpid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# get the event and utxo from a txid
@app.get("/getEventAndUtxo")
def getEventAndUtxo(txid: str):
    if eth is None:
        raise HTTPException(status_code=500, detail="Ethereum interface is not initialized")

    try:
        event, utxo = eth.get_event_and_utxo(txid)
        return {"event": event, "utxo": utxo}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
