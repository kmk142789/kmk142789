# EchoWorld Bootstrap

The **EchoWorldBootstrap** module is a thin orchestration layer that brings together the experimental cognition features in `innovation_suite` with the offline-first `OuterLinkRuntime`. It is designed to be safe for CI and local testing by default, avoiding heavy network behaviour while still exercising the wiring between components.

## Running from Python

Use the module entrypoint to perform a dry run (recommended for CI and quick validation):

```bash
python -m echo.echo_world_bootstrap --dry-run
```

To emit the status as JSON:

```bash
python -m echo.echo_world_bootstrap --json
```

## Running from Termux

A Termux-friendly launcher is available at `outerlink/echo_world_termux.sh`:

```bash
bash outerlink/echo_world_termux.sh
```

The script first performs a dry run to validate the environment and then, if successful, triggers the live bootstrap.

## Repository link

Track updates and clone the project directly from the main repository: https://github.com/kmk142789/kmk142789

## Dry run safety

The `dry_run` option instantiates components and performs lightweight sanity checks without blocking loops or heavy network I/O, making it suitable for CI pipelines and offline testing scenarios.
