"""Publish/subscribe message bus used across Atlas subsystems."""

from __future__ import annotations

import logging
import threading
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Deque, DefaultDict, Dict, Iterable, List, Optional

_LOGGER = logging.getLogger(__name__)


@dataclass
class Subscription:
    topic: str
    callback: Callable[[str, Dict], None]
    priority: int = 0
    lane: str = "default"


class MessageBus:
    """Lightweight synchronous message bus with replay buffers."""

    def __init__(self, replay: int = 128) -> None:
        self._subscriptions: DefaultDict[str, List[Subscription]] = defaultdict(list)
        self._replay: DefaultDict[str, Deque[Dict]] = defaultdict(lambda: deque(maxlen=replay))
        self._lock = threading.RLock()

    def subscribe(
        self,
        topic: str,
        callback: Callable[[str, Dict], None],
        *,
        priority: int = 0,
        lane: str = "default",
        replay: bool = True,
    ) -> Subscription:
        sub = Subscription(topic, callback, priority, lane)
        with self._lock:
            subs = self._subscriptions[topic]
            subs.append(sub)
            subs.sort(key=lambda s: s.priority, reverse=True)
            if replay:
                for message in self._replay[topic]:
                    try:
                        callback(topic, message)
                    except Exception:  # pragma: no cover
                        _LOGGER.exception("Replay delivery failed for %s", topic)
        _LOGGER.debug("Subscription added for topic %s priority=%s", topic, priority)
        return sub

    def unsubscribe(self, subscription: Subscription) -> None:
        with self._lock:
            subs = self._subscriptions[subscription.topic]
            if subscription in subs:
                subs.remove(subscription)
                _LOGGER.debug("Subscription removed for %s", subscription.topic)

    def publish(self, topic: str, payload: Dict, *, lane_hint: Optional[str] = None) -> None:
        """Publish ``payload`` to ``topic`` for all subscribers."""

        with self._lock:
            self._replay[topic].append(payload)
            subs = list(self._subscriptions.get(topic, []))
        for sub in subs:
            lane = lane_hint or sub.lane
            try:
                _LOGGER.debug("Delivering message on topic %s lane=%s", topic, lane)
                sub.callback(topic, {**payload, "lane": lane})
            except Exception:  # pragma: no cover
                _LOGGER.exception("Subscriber %s raised", sub.callback)

    def topics(self) -> Iterable[str]:
        return list(self._subscriptions.keys())


__all__ = ["MessageBus", "Subscription"]
