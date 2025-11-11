import time

from atlas_network import TokenBucketLimiter


def test_token_bucket_limiter_refills_tokens():
    limiter = TokenBucketLimiter(rate=10, capacity=10)
    assert limiter.consume(5) is True
    assert limiter.consume(6) is False
    time.sleep(0.2)
    assert limiter.available() > 0
