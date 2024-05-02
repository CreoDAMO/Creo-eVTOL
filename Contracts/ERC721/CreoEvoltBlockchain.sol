// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableMap.sol"; // Import EnumerableMap contract

contract EVTolToken is ERC721 {
    using EnumerableMap for EnumerableMap.UintToAddressMap; // Use EnumerableMap for UintToAddressMap

    // Struct to store eVTOL metadata
    struct EVTOLOwner {
        string identifier; // Unique identifier of the eVTOL
        string inspectionHistory; // Inspection history of the eVTOL
        // Add additional metadata as needed
    }
    
    // Mapping to store eVTOL metadata
    mapping(uint256 => EVTOLOwner) private _eVTOLData;
    EnumerableMap.UintToAddressMap private _tokenOwners; // Track token ownership
    
    // Constructor to initialize the ERC721 contract with name "eVTOL" and symbol "EVTOL"
    constructor() ERC721("eVTOL", "EVTOL") {}

    // Function to mint a new eVTOL NFT
    function mintEVTOLOwner(address to, uint256 tokenId, string memory identifier, string memory inspectionHistory) external {
        _mint(to, tokenId); // Mint a new token with the specified tokenId and assign it to the specified address
        _eVTOLData[tokenId] = EVTOLOwner(identifier, inspectionHistory); // Store metadata for the minted eVTOL token
    }
    
    // Function to get eVTOL metadata
    function getEVTOLOwnerMetadata(uint256 tokenId) external view returns (string memory identifier, string memory inspectionHistory) {
        require(_tokenOwners.contains(tokenId), "Token ID does not exist"); // Ensure that the token exists
        return (_eVTOLData[tokenId].identifier, _eVTOLData[tokenId].inspectionHistory); // Return metadata for the specified eVTOL token
    }
    
    // Other functions for your ERC-721 contract...
}
