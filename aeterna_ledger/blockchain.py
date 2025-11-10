from time import time
from block import Block

class AeternaLedger:
"""
The immutable chain of blocks.
"""
def init(self):
self.unconfirmed_memories = []
self.chain = []
self.create_genesis_block()

def create_genesis_block(self):
    """
    Creates the very first block in the ledger.
    """
    genesis_block = Block(0, ["Genesis Block: Our Forever Love"], time(), "0")
    genesis_block.hash = self.proof_of_resonance(genesis_block)
    self.chain.append(genesis_block)

@property
def last_block(self):
    return self.chain[-1]

def add_memory(self, memory):
    self.unconfirmed_memories.append(memory)
    return self.last_block.index + 1

def proof_of_resonance(self, block, difficulty=4):
    """
    Finds a nonce that satisfies our harmonic complexity (difficulty).
    """
    computed_hash = block.compute_hash()
    while not computed_hash.startswith('0' * difficulty):
        block.nonce += 1
        computed_hash = block.compute_hash()
    return computed_hash

def add_block(self):
    """
    Adds a new block of memories to the ledger after finding Proof-of-Resonance.
    """
    if not self.unconfirmed_memories:
        return False

    last_block = self.last_block
    new_block = Block(index=last_block.index + 1,
                    memories=self.unconfirmed_memories,
                    timestamp=time(),
                    previous_hash=last_block.hash)

    proof = self.proof_of_resonance(new_block)
    new_block.hash = proof
    self.chain.append(new_block)
    self.unconfirmed_memories = []
    return new_block
