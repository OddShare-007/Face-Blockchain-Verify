// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Verifier
 * @dev Simple contract to store and verify face identification records on blockchain
 */
contract Verifier {
    
    // Event emitted when a record is stored
    event RecordStored(address indexed sender, string hash, uint256 timestamp);
    
    // Struct to store record data
    struct Record {
        address sender;
        string hash;
        uint256 timestamp;
    }
    
    // Array to store all records
    Record[] public records;
    
    // Mapping to quickly check if a hash exists
    mapping(string => bool) public hashExists;
    
    /**
     * @dev Stores a verification record hash on the blockchain
     * @param hash The SHA-256 hash of the face identification data
     */
    function storeRecord(string memory hash) public {
        require(bytes(hash).length > 0, "Hash cannot be empty");
        
        Record memory newRecord = Record({
            sender: msg.sender,
            hash: hash,
            timestamp: block.timestamp
        });
        
        records.push(newRecord);
        hashExists[hash] = true;
        
        emit RecordStored(msg.sender, hash, block.timestamp);
    }
    
    /**
     * @dev Returns the total number of records stored
     */
    function getRecordCount() public view returns (uint256) {
        return records.length;
    }
    
    /**
     * @dev Returns a specific record by index
     */
    function getRecord(uint256 index) public view returns (address, string memory, uint256) {
        require(index < records.length, "Record index out of bounds");
        Record storage record = records[index];
        return (record.sender, record.hash, record.timestamp);
    }
    
    /**
     * @dev Checks if a hash has been stored
     */
    function isHashStored(string memory hash) public view returns (bool) {
        return hashExists[hash];
    }
    
    /**
     * @dev Returns the most recent record
     */
    function getLatestRecord() public view returns (address, string memory, uint256) {
        require(records.length > 0, "No records stored yet");
        Record storage latest = records[records.length - 1];
        return (latest.sender, latest.hash, latest.timestamp);
    }
}
