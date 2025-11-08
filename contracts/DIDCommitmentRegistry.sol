// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title DIDCommitmentRegistry
/// @notice Stores cross-chain DID commitments derived from Merkle + zk proof material.
/// @dev The registry accepts a pre-computed aggregate commitment that must equal
///      keccak256(didHash || credentialRoot || zkCommitment).  Merkle proofs are
///      verified with Keccak hashing to mirror off-chain tooling.
contract DIDCommitmentRegistry {
    struct Commitment {
        bytes32 didHash;
        bytes32 credentialRoot;
        bytes32 zkCommitment;
        bytes32 aggregateCommitment;
        address submitter;
        uint64 timestamp;
    }

    mapping(bytes32 => Commitment) private commitments;

    event CommitmentRegistered(bytes32 indexed didKey, address indexed submitter, bytes32 aggregateCommitment);
    event CommitmentRevoked(bytes32 indexed didKey, address indexed submitter);

    error AggregateMismatch();
    error CommitmentNotFound();
    error Unauthorized();

    /// @notice Register or update a DID commitment tuple.
    /// @param didKey keccak256 hash of the DID identifier used as the registry key.
    /// @param didHash keccak256 hash of the canonical DID document.
    /// @param credentialRoot Keccak Merkle root for credential proof set.
    /// @param zkCommitment Commitment digest produced by a zk proof system.
    /// @param aggregateCommitment Combined hash of the tuple used for cross-chain anchoring.
    function registerCommitment(
        bytes32 didKey,
        bytes32 didHash,
        bytes32 credentialRoot,
        bytes32 zkCommitment,
        bytes32 aggregateCommitment
    ) external {
        if (aggregateCommitment != keccak256(abi.encodePacked(didHash, credentialRoot, zkCommitment))) {
            revert AggregateMismatch();
        }

        commitments[didKey] = Commitment({
            didHash: didHash,
            credentialRoot: credentialRoot,
            zkCommitment: zkCommitment,
            aggregateCommitment: aggregateCommitment,
            submitter: msg.sender,
            timestamp: uint64(block.timestamp)
        });

        emit CommitmentRegistered(didKey, msg.sender, aggregateCommitment);
    }

    /// @notice Remove a commitment from the registry.
    /// @param didKey Hash key for the DID commitment.
    function revokeCommitment(bytes32 didKey) external {
        Commitment memory record = commitments[didKey];
        if (record.submitter == address(0)) {
            revert CommitmentNotFound();
        }
        if (record.submitter != msg.sender) {
            revert Unauthorized();
        }
        delete commitments[didKey];
        emit CommitmentRevoked(didKey, msg.sender);
    }

    /// @notice Retrieve the stored tuple for a DID key.
    function getCommitment(bytes32 didKey) external view returns (Commitment memory) {
        Commitment memory record = commitments[didKey];
        if (record.submitter == address(0)) {
            revert CommitmentNotFound();
        }
        return record;
    }

    /// @notice Verify a Merkle leaf against the stored credential root.
    /// @param didKey Key referencing the stored commitment tuple.
    /// @param leafHash Hash of the credential leaf (Keccak).
    /// @param index Zero-based index for the credential leaf.
    /// @param proof Array of sibling hashes required to reconstruct the root.
    function verifyCredentialLeaf(
        bytes32 didKey,
        bytes32 leafHash,
        uint256 index,
        bytes32[] calldata proof
    ) external view returns (bool) {
        Commitment memory record = commitments[didKey];
        if (record.submitter == address(0)) {
            revert CommitmentNotFound();
        }
        bytes32 computed = _computeRootFromProof(leafHash, proof, index);
        return computed == record.credentialRoot;
    }

    /// @notice Verify that an aggregate commitment matches the stored tuple.
    function verifyAggregate(bytes32 didKey, bytes32 aggregateCommitment) external view returns (bool) {
        Commitment memory record = commitments[didKey];
        if (record.submitter == address(0)) {
            revert CommitmentNotFound();
        }
        return record.aggregateCommitment == aggregateCommitment;
    }

    /// @notice Verify that a zk commitment matches the stored tuple.
    function verifyZkCommitment(bytes32 didKey, bytes32 zkCommitment) external view returns (bool) {
        Commitment memory record = commitments[didKey];
        if (record.submitter == address(0)) {
            revert CommitmentNotFound();
        }
        return record.zkCommitment == zkCommitment;
    }

    function _computeRootFromProof(
        bytes32 leaf,
        bytes32[] calldata proof,
        uint256 index
    ) internal pure returns (bytes32) {
        bytes32 computed = leaf;
        for (uint256 i = 0; i < proof.length; i++) {
            bytes32 sibling = proof[i];
            if (index % 2 == 0) {
                computed = keccak256(abi.encodePacked(computed, sibling));
            } else {
                computed = keccak256(abi.encodePacked(sibling, computed));
            }
            index /= 2;
        }
        return computed;
    }
}
