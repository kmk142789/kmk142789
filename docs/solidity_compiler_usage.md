# Solidity Compiler Quick Reference

This guide captures the essentials for working with the Solidity command-line compiler (`solc`). Use it as a quick refresher when preparing or auditing smart contract build pipelines inside the repository.

## Basic Invocation

- Run `solc --help` to review every available switch.
- `solc --bin sourceFile.sol` compiles a single contract file and prints the runtime bytecode to stdout.
- Combine `-o <dir>` with specific flags (for example, `--bin`, `--ast-compact-json`, `--asm`) to persist each output artifact inside the chosen directory.

## Optimizer Configuration

- Enable the optimizer with `--optimize`; override the expected call frequency with `--optimize-runs=<runs>`.
- Lower run counts bias toward cheaper deployment at the cost of more expensive function calls. Higher run counts assume frequent execution and prioritize lower runtime gas usage.
- Optimizer choices influence dispatch table size, literal storage layout, and other code generation strategies.

## Managing Imports

- The compiler automatically resolves relative imports from the filesystem.
- Remap import prefixes with `prefix=path`, e.g. `solc github.com/ethereum/dapp-bin/=/usr/local/lib/dapp-bin/ file.sol`.
- Use `--base-path`, `--include-path`, and `--allow-paths` to control which directories `solc` may read for sources and dependencies. Paths provided on the command line are implicitly trusted.

## Library Linking

- Unlinked bytecode contains placeholders such as `__$53aea86b7d70b31448b230b20ae141a537$__` that reference fully qualified library names.
- Supply concrete addresses with `--libraries "file.sol:Math=0x1234..."` or by passing a file that lists mappings (one per line).
- Prefer linking during compilation so that the contract metadata remains consistent.

## Choosing an EVM Target

- Set the target hard fork with `--evm-version <version>`. Supported identifiers range from historical forks (e.g. `homestead`, `byzantium`) to the newest releases (`prague`, `osaka`).
- Targeting the correct fork ensures opcodes, gas costs, and available language features match the chain environment.

### Fork Highlights

- **tangerineWhistle**: increased inter-account access gas; external calls forward full gas by default.
- **spuriousDragon**: higher `EXP` cost.
- **byzantium**: introduces `returndatacopy`, `returndatasize`, `staticcall`, and `revert`.
- **constantinople / petersburg**: adds `create2`, `extcodehash`, bitwise shift opcodes.
- **istanbul**: enables `chainid` and `selfbalance`.
- **berlin**: adjusts gas accounting for storage and balance opcodes.
- **london**: exposes `block.basefee`.
- **paris**: replaces `block.difficulty` with `block.prevrandao` semantics.
- **shanghai**: supports the zero push opcode (`push0`).
- **cancun**: introduces blob transaction helpers (`blobbasefee`, `blobhash`, `mcopy`, `tstore`, `tload`).
- **osaka**: experimental compilation targeting the EOF container format.

## JSON Compiler Interface

- The preferred automation path is `solc --standard-json`, which reads JSON from stdin and returns JSON on stdout.
- Inputs must specify the language (`"Solidity"`, `"Yul"`, etc.), a `sources` mapping, and optional `settings` (optimizer, remappings, EVM version, EOF version).
- Outputs include compiled artifacts, diagnostics, and metadata. The process exit code is always zero; rely on the JSON payload for error reporting.

Use this document alongside the upstream Solidity documentation when configuring build scripts or CI jobs.
