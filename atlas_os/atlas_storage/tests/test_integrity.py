from atlas_storage import DistributedVirtualFileSystem, IntegrityChecker, SnapshotManager, TransactionLog
from atlas_storage.atlas_storage.drivers.memory import MemoryFileDriver
from atlas_storage.atlas_storage.vfs import StorageNode


def test_integrity_checker_detects_changes(tmp_path):
    log = TransactionLog()
    vfs = DistributedVirtualFileSystem(log)
    driver = MemoryFileDriver()
    vfs.register_node(StorageNode("mem", driver, 1024))
    vfs.write("foo.txt", b"hello")
    checker = IntegrityChecker(vfs)
    manifest = checker.manifest()
    assert checker.verify(manifest)
    vfs.write("foo.txt", b"bye")
    assert not checker.verify(manifest)


def test_snapshot_and_rollback(tmp_path):
    log = TransactionLog()
    vfs = DistributedVirtualFileSystem(log)
    driver = MemoryFileDriver()
    vfs.register_node(StorageNode("mem", driver, 1024))
    vfs.write("foo.txt", b"hello")
    snapshots = SnapshotManager(vfs)
    snapshots.create("baseline")
    vfs.write("foo.txt", b"mutated")
    snapshots.rollback("baseline")
    assert vfs.read("foo.txt") == b"hello"
