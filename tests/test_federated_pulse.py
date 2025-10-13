"""Tests for the Federated Pulse CRDT and gossip simulation."""
import time

from federated_pulse.gossip_sim import Node, simulate
from federated_pulse.lww_map import LWWMap


def test_lww_basic_merge():
    a = LWWMap("A")
    b = LWWMap("B")
    ts = int(time.time() * 1000)
    a.assign("x", "one", ts)
    b.assign("x", "two", ts + 1)
    m = a.merge(b)
    assert m.get("x") == "two"
    m2 = b.merge(a)
    assert m2.get("x") == "two"
    m3 = m.merge(m2)
    assert m3.get("x") == "two"


def test_gossip_convergence():
    nodes = [Node(f"N{i}") for i in range(5)]
    hist = simulate(nodes, steps=50, seed=99, p_partition=0.2)
    assert hist[-1] == 1 or hist[-2] == 1
