//! Native Solana program that mirrors the Ethereum DID commitment registry logic.
//!
//! The program does not persist state; instead, it provides stateless verification
//! routines that can be invoked from off-chain clients or CPI callers.  Each
//! instruction validates that the Merkle proof, aggregate commitment, and
//! Ed25519 signature match the shared hash commitments produced by the
//! cross-chain tooling in `packages/core`.

use borsh::{BorshDeserialize, BorshSerialize};
use ed25519_dalek::{Signature, SigningKey, VerifyingKey, Verifier};
use sha3::{Digest, Keccak256};
use solana_program::{
    account_info::AccountInfo,
    entrypoint,
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    pubkey::Pubkey,
};
use thiserror::Error;

/// 32-byte hash used throughout the program.
pub type Hash = [u8; 32];

#[derive(BorshSerialize, BorshDeserialize, Clone, Debug, PartialEq, Eq)]
pub struct CommitmentTuple {
    pub did_hash: Hash,
    pub credential_root: Hash,
    pub zk_commitment: Hash,
    pub aggregate_commitment: Hash,
}

impl CommitmentTuple {
    pub fn recompute_aggregate(&self) -> Hash {
        let mut hasher = Keccak256::new();
        hasher.update(self.did_hash);
        hasher.update(self.credential_root);
        hasher.update(self.zk_commitment);
        hasher.finalize().into()
    }
}

#[derive(BorshSerialize, BorshDeserialize, Clone, Debug, PartialEq, Eq)]
pub struct VerifyInstruction {
    pub commitment: CommitmentTuple,
    pub credential_leaf: Hash,
    pub index: u64,
    pub merkle_proof: Vec<Hash>,
    pub ed25519_public_key: [u8; 32],
    pub ed25519_signature: [u8; 64],
}

#[derive(Error, Debug, Copy, Clone)]
pub enum DidCommitmentError {
    #[error("aggregate commitment mismatch")]
    AggregateMismatch,
    #[error("merkle proof invalid")]
    InvalidMerkleProof,
    #[error("signature verification failed")]
    SignatureInvalid,
    #[error("instruction deserialize error")]
    DeserializeFailed,
}

impl From<DidCommitmentError> for ProgramError {
    fn from(value: DidCommitmentError) -> Self {
        ProgramError::Custom(value as u32)
    }
}

entrypoint!(process_instruction);

pub fn process_instruction(
    _program_id: &Pubkey,
    _accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let instruction = VerifyInstruction::try_from_slice(instruction_data)
        .map_err(|_| ProgramError::from(DidCommitmentError::DeserializeFailed))?;

    verify_commitment(&instruction)?;
    Ok(())
}

pub fn verify_commitment(instruction: &VerifyInstruction) -> Result<(), ProgramError> {
    let recomputed = instruction.commitment.recompute_aggregate();
    if recomputed != instruction.commitment.aggregate_commitment {
        msg!("aggregate mismatch: expected {:?} got {:?}", instruction.commitment.aggregate_commitment, recomputed);
        return Err(DidCommitmentError::AggregateMismatch.into());
    }

    let leaf_root = compute_merkle_root(
        instruction.credential_leaf,
        &instruction.merkle_proof,
        instruction.index,
    );

    if leaf_root != instruction.commitment.credential_root {
        msg!("invalid merkle proof");
        return Err(DidCommitmentError::InvalidMerkleProof.into());
    }

    let verifying_key = VerifyingKey::from_bytes(&instruction.ed25519_public_key)
        .map_err(|_| DidCommitmentError::SignatureInvalid)?;
    let signature = Signature::from_bytes(&instruction.ed25519_signature)
        .map_err(|_| DidCommitmentError::SignatureInvalid)?;

    verifying_key
        .verify_strict(&instruction.commitment.aggregate_commitment, &signature)
        .map_err(|_| DidCommitmentError::SignatureInvalid.into())
}

fn compute_merkle_root(leaf: Hash, proof: &[Hash], mut index: u64) -> Hash {
    let mut computed = leaf;
    for sibling in proof {
        let mut hasher = Keccak256::new();
        if index % 2 == 0 {
            hasher.update(computed);
            hasher.update(sibling);
        } else {
            hasher.update(sibling);
            hasher.update(computed);
        }
        computed = hasher.finalize().into();
        index /= 2;
    }
    computed
}

/// Convenience helper used in tests and examples for creating signatures.
pub fn sign_commitment(commitment: &CommitmentTuple, signing_key: &SigningKey) -> [u8; 64] {
    signing_key.sign(&commitment.aggregate_commitment).to_bytes()
}
