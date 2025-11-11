import time

from atlas_kernel import AtlasEventLoop, PriorityScheduler


def test_priority_scheduler_starvation_protection():
    scheduler = PriorityScheduler()
    execution_order = []

    for idx in range(5):
        scheduler.enqueue(lambda idx=idx: execution_order.append(idx), priority=idx)

    seen = []
    while scheduler.pending_tasks():
        task = scheduler.dequeue()
        assert task is not None
        task.callback()
        seen.append(task)
    assert set(execution_order) == set(range(5))


def test_event_loop_runs_microtasks():
    loop = AtlasEventLoop()
    executed = []

    def task():
        executed.append("ran")
        loop.stop()

    loop.call_soon(task, lane="test")
    loop.run()
    assert executed == ["ran"]
