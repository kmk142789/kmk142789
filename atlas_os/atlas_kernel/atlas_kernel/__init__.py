"""Atlas Kernel package exposing the primary runtime primitives.

The kernel is implemented entirely in Python but follows a microkernel
architecture that mirrors real-time operating systems.  Each
subsystem is exposed via this package to make consumption from other
modules straightforward.  The kernel focuses on cooperatively
scheduled user tasks with priority lanes, a message bus for
communication, and resource management/metrics reporting utilities.
"""

from .event_loop import AtlasEventLoop
from .scheduler import PriorityScheduler, ScheduledTask
from .message_bus import MessageBus
from .resource_manager import ResourceBudget, ResourceManager
from .metrics import KernelMetricsExporter
from .diagnostics import KernelDiagnostics, KernelEvent
from .timebase import Timebase
from .task_registry import TaskRegistry, TaskRecord
from .watchdog import EventLoopWatchdog

__all__ = [
    "AtlasEventLoop",
    "PriorityScheduler",
    "ScheduledTask",
    "MessageBus",
    "ResourceBudget",
    "ResourceManager",
    "KernelMetricsExporter",
    "KernelDiagnostics",
    "KernelEvent",
    "Timebase",
    "TaskRegistry",
    "TaskRecord",
    "EventLoopWatchdog",
]
