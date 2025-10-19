from echo.echo_codox_kernel import EchoCodexKernel


def main():
    kernel = EchoCodexKernel()
    print(f"Events: {len(kernel.history)}")
    print(f"Resonance: {kernel.resonance()}")


if __name__ == "__main__":
    main()
