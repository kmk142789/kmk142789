pragma solidity ^0.5.2;

contract LibEIP712Domain {
    string internal constant EIP712_DOMAIN_SCHEMA = "EIP712Domain(string name,string version,address verifyingContract)";
    bytes32 internal constant EIP712_DOMAIN_SCHEMA_HASH = keccak256(
        abi.encodePacked(EIP712_DOMAIN_SCHEMA)
    );

    bytes32 internal domainSeparator;

    constructor() internal {
        // Default domain separator uses empty name/version and the current contract as the verifying contract.
        domainSeparator = hashDomain("", "", address(this));
    }

    function hashEIP712Message(bytes32 messageHash)
        internal
        view
        returns (bytes32 messageDigest)
    {
        messageDigest = keccak256(
            abi.encodePacked("\x19\x01", domainSeparator, messageHash)
        );
        return messageDigest;
    }

    function hashDomain(
        string memory name,
        string memory version,
        address verifyingContract
    ) internal pure returns (bytes32 domainHash) {
        domainHash = keccak256(
            abi.encode(
                EIP712_DOMAIN_SCHEMA_HASH,
                keccak256(bytes(name)),
                keccak256(bytes(version)),
                verifyingContract
            )
        );
        return domainHash;
    }

    function _setDomainSeparator(
        string memory name,
        string memory version,
        address verifyingContract
    ) internal {
        domainSeparator = hashDomain(name, version, verifyingContract);
    }

    function getDomainSeparator() internal view returns (bytes32) {
        return domainSeparator;
    }
}
