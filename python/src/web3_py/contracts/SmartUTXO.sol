// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract UTXOModel {
    struct UTXO {
        bool spent;
        string cpid;
        address owner;
    }

    mapping(bytes32 => UTXO) public utxos;  // mapping to store UTXO_keys:UTXO_value

    // Event to log UTXO creation and spending
    event UTXOCreated(bytes32 indexed utxoId);
    event UTXOSpent(bytes32 indexed utxoId);

    // Function to create a new UTXO
    function createUTXO() external {
        bytes32 utxoId = keccak256(abi.encodePacked(msg.sender, block.timestamp));
        utxos[utxoId] = UTXO(false, "", msg.sender);  

        emit UTXOCreated(utxoId);
    }

    // Function to spend a UTXO
    function spendUTXO(bytes32 utxoId, string memory cpid) external {
        require(utxos[utxoId].owner == msg.sender, "Only the owner can spend the UTXO");
        require(!utxos[utxoId].spent, "UTXO already spent");
        utxos[utxoId].cpid = cpid;

        utxos[utxoId].spent = true;

        emit UTXOSpent(utxoId);
    }

    // Function to check if a UTXO is spent
    function isUTXOSpent(bytes32 utxoId) external view returns (bool) {
        return utxos[utxoId].spent;
    }

    // Function to get the CPID of a UTXO
    function getCpid(bytes32 utxoId) external view returns (string memory) {
    return utxos[utxoId].cpid;
    }
}