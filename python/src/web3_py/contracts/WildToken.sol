pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";


contract WilderToken is ERC20 {
    address public owner;

    constructor() ERC20("WilderToken", "WTK") {
        owner = msg.sender;
        _mint(msg.sender, 1 * (10 ** uint256(decimals()))); // Mint 1 token upon deployment
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can perform this action");
        _;
    }


    function transfer(address , uint256 ) public pure override returns (bool) {
        revert("Token transfers are disabled");
    }

    function transferFrom(address , address , uint256 ) public pure override returns (bool) {
        revert("Token transfers are disabled");
    }

    function approve(address , uint256 ) public pure override returns (bool) {
        revert("Token transfers are disabled");
    }


    // Owner-only function to burn the token (destroy it permanently)
    function burn() public onlyOwner {
        _burn(msg.sender, balanceOf(msg.sender)); // Burn the entire token balance of the owner
    }

    function totalSupply() public view override returns (uint256) {
        return 1 * (10 ** uint256(decimals())); // Fixed total supply of 1 token
    }
}
