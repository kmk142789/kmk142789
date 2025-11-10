import hashlib
import json
from time import time

class Block:
"""
A single block in the Aeterna Ledger.
"""
def init(self, index, memories, timestamp, previous_hash, nonce=0):
self.index = index
self.memories = memories
self.timestamp = timestamp
self.previous_hash = previous_hash
self.nonce = nonce

def compute_hash(self):
    """
    Computes the hash for the entire block.
    """
    block_string = json.dumps(self.__dict__, sort_keys=True)
    return hashlib.sha256(block_string.encode()).hexdigest()
