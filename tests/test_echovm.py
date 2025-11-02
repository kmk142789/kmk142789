import textwrap
import uuid

from echo.echovm import (
    EchoVM,
    VirtualFileSystem,
    assemble,
    create_vm,
    device,
    register_default_syscalls,
    register_devices,
)


def test_run_simple_arithmetic_program(capsys):
    program = textwrap.dedent(
        """
        PUSH 2
        PUSH 3
        ADD
        PRINT
        HALT
        """
    )
    vm = create_vm(program, install_default_syscalls=False, install_devices=False)
    vm.run()
    captured = capsys.readouterr().out.strip().splitlines()
    assert captured == ["5"]


def test_virtual_filesystem_roundtrip(capsys):
    program = textwrap.dedent(
        """
        ; write value "hello" to key "greet"
        PUSH 103
        PUSH 114
        PUSH 101
        PUSH 101
        PUSH 116
        PUSH 5
        PUSH 104
        PUSH 101
        PUSH 108
        PUSH 108
        PUSH 111
        PUSH 5
        SYS 10
        ; read the value back and print it
        PUSH 103
        PUSH 114
        PUSH 101
        PUSH 101
        PUSH 116
        PUSH 5
        SYS 11
        SYS 1
        HALT
        """
    )
    vfs = VirtualFileSystem()
    vm = create_vm(install_default_syscalls=False, install_devices=False, vfs=vfs)
    register_default_syscalls(vm, vfs=vfs)
    vm.load(assemble(program))
    vm.run()
    output = capsys.readouterr().out.strip().splitlines()
    assert output == ["hello"]
    assert vfs.read("greet") == "hello"


def test_device_plugin_registration(capsys):
    syscall_number = 99
    name = f"test_double_{uuid.uuid4().hex}"

    @device(name, number=syscall_number)
    def _double(vm: EchoVM, stack):
        value = vm.pop()
        vm.push(value * 2)

    vm = create_vm(install_default_syscalls=False, install_devices=False)
    register_devices(vm, names=[name])

    program = textwrap.dedent(
        f"""
        PUSH 21
        SYS {syscall_number}
        PRINT
        HALT
        """
    )
    vm.load(assemble(program))
    vm.run()
    captured = capsys.readouterr().out.strip().splitlines()
    assert captured == ["42"]
