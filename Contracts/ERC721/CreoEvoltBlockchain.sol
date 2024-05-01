// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "./interfaces/IIdentity.sol";
import "./interfaces/IPaymentChannels.sol";
import "./interfaces/IOracle.sol";

contract CreoEvtolBlockchain is ERC721, AccessControl, Ownable, Pausable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    // Roles
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant REGULATOR_ROLE = keccak256("REGULATOR_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    // Mapping from EVTOL ID to telemetry data hash
    mapping(string => bytes32) private telemetryData;

    // Mapping from EVTOL ID to maintenance history
    mapping(string => string[]) private maintenanceHistory;

    // Mapping from EVTOL ID to NFT token ID
    mapping(string => uint256) private evtolToTokenId;

    // Interfaces for external contracts and systems
    IIdentity public identityContract;
    IPaymentChannels public paymentChannelsContract;
    IOracle public oracleContract;

    constructor(
        address _identityContractAddress,
        address _paymentChannelsContractAddress,
        address _oracleContractAddress
    ) ERC721("CreoEvtol", "EVTOL") {
        _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
        identityContract = IIdentity(_identityContractAddress);
        paymentChannelsContract = IPaymentChannels(_paymentChannelsContractAddress);
        oracleContract = IOracle(_oracleContractAddress);
    }

    function pause() public onlyRole(ADMIN_ROLE) {
        _pause();
    }

    function unpause() public onlyRole(ADMIN_ROLE) {
        _unpause();
    }

    function logTelemetryData(string memory evtolId, bytes32 dataHash) public whenNotPaused onlyRole(OPERATOR_ROLE) {
        telemetryData[evtolId] = dataHash;
    }

    function performMaintenance(string memory evtolId, string memory record) public whenNotPaused onlyRole(OPERATOR_ROLE) {
        maintenanceHistory[evtolId].push(record);
    }

    function mintEvtolNFT(string memory evtolId) public whenNotPaused onlyRole(OPERATOR_ROLE) {
        _tokenIdCounter.increment();
        uint256 tokenId = _tokenIdCounter.current();
        evtolToTokenId[evtolId] = tokenId;
        _mint(msg.sender, tokenId);
    }

    function verifyFlightPath(string memory evtolId, string memory flightData) public whenNotPaused onlyRole(REGULATOR_ROLE) {
        // Add flight path verification logic
        require(oracleContract.verifyFlightData(flightData), "Flight data verification failed");
    }

    function openPaymentChannel(address recipient, uint256 amount) public whenNotPaused onlyRole(OPERATOR_ROLE) {
        paymentChannelsContract.openChannel(msg.sender, recipient, amount);
    }

    function closePaymentChannel(address recipient) public whenNotPaused onlyRole(OPERATOR_ROLE) {
        paymentChannelsContract.closeChannel(msg.sender, recipient);
    }

    function getTelemetryData(string memory evtolId) public view returns (bytes32) {
        return telemetryData[evtolId];
    }

    function getMaintenanceHistory(string memory evtolId) public view returns (string[] memory) {
        return maintenanceHistory[evtolId];
    }

    function getTokenIdForEvtol(string memory evtolId) public view returns (uint256) {
        return evtolToTokenId[evtolId];
    }

    // Role management functions
    function grantRole(bytes32 role, address account) public onlyRole(ADMIN_ROLE) {
        grantRole(role, account);
    }

    function revokeRole(bytes32 role, address account) public onlyRole(ADMIN_ROLE) {
        revokeRole(role, account);
    }

    function renounceRole(bytes32 role, address account) public {
        renounceRole(role, account);
    }
}
