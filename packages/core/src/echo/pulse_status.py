from __future__ import annotations

import argparse
import os
from typing import Sequence

from echo.echo_codox_kernel import EchoCodexKernel
from echo.echo_recursive_reflection_kernel import EchoRecursiveReflectionKernel

_KERNELS = {
    "codex": EchoCodexKernel,
    "recursive_reflection": EchoRecursiveReflectionKernel,
}


def _default_kernel() -> str:
    env_value = os.environ.get("ECHO_PULSE_KERNEL", "").strip().lower()
    return env_value if env_value in _KERNELS else "codex"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect Echo pulse kernel state")
    parser.add_argument(
        "--kernel",
        choices=sorted(_KERNELS.keys()),
        default=_default_kernel(),
        help="Kernel to instantiate (default: %(default)s)",
    )
    parser.add_argument(
        "--recursion-depth",
        type=int,
        default=None,
        help="Number of recursive reflection cycles to generate",
    )
    parser.add_argument(
        "--render-reflections",
        action="store_true",
        help="Render the generated reflections when using the recursive kernel",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    kernel_name = args.kernel
    kernel_type = _KERNELS[kernel_name]

    if kernel_name == "recursive_reflection":
        depth = args.recursion_depth if args.recursion_depth is not None else 3
        kernel = kernel_type(recursion_depth=depth)
        print(f"Reflections: {len(kernel.history)}")
        print(f"Resonance: {kernel.resonance()}")
        if args.render_reflections and kernel.history:
            print("")
            print(kernel.summary())
    else:
        kernel = kernel_type()
        print(f"Events: {len(kernel.history)}")
        print(f"Resonance: {kernel.resonance()}")


if __name__ == "__main__":
    main()
