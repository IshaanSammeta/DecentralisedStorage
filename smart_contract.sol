pragma solidity ^0.8.0;

contract EncryptedIPFSStorage {
    mapping(address => bytes) private encryptedHashes;

    event EncryptedHashStored(address indexed user, bytes encryptedHash);

    // Function to store encrypted IPFS hash
    function storeEncryptedHash(bytes memory encryptedHash) public {
        encryptedHashes[msg.sender] = encryptedHash;
        emit EncryptedHashStored(msg.sender, encryptedHash);
    }

    // Function to retrieve encrypted IPFS hash
    function getEncryptedHash(address user) public view returns (bytes memory) {
        return encryptedHashes[user];
    }
}
