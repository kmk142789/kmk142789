import time

from atlas_storage import SegmentCache


def test_segment_cache_respects_ttl():
    cache: SegmentCache[str, int] = SegmentCache(capacity=2, ttl=0.05)
    cache.put('a', 1)
    assert cache.get('a') == 1
    time.sleep(0.1)
    assert cache.get('a') is None


def test_segment_cache_eviction():
    cache: SegmentCache[str, int] = SegmentCache(capacity=2, ttl=1)
    cache.put('a', 1)
    cache.put('b', 2)
    cache.put('c', 3)
    assert cache.get('a') is None
    assert cache.get('b') == 2
    assert cache.get('c') == 3
