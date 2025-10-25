# Solidity Compiler Quick Reference

This guide captures the essentials for working with the Solidity command-line compiler (`solc`). Use it as a quick refresher when preparing or auditing smart contract build pipelines inside the repository.

## Basic Invocation

- Run `solc --help` to review every available switch.
- `solc --bin sourceFile.sol` compiles a single contract file and prints the runtime bytecode to stdout.
- Combine `-o <dir>` with specific flags (for example, `--bin`, `--ast-compact-json`, `--asm`) to persist each output artifact inside the chosen directory.
- For batch compilation, prefer `solc -o <dir> --bin --abi file1.sol file2.sol` so that each contract is emitted to its own artifact in the designated folder.
- Use `solc --standard-json` for structured input/output that always returns JSON on stdout even when compilation errors occur.

## Optimizer Configuration

- Enable the optimizer with `--optimize`; override the expected call frequency with `--optimize-runs=<runs>`.
- Lower run counts bias toward cheaper deployment at the cost of more expensive function calls. Higher run counts assume frequent execution and prioritize lower runtime gas usage.
- Optimizer choices influence dispatch table size, literal storage layout, and other code generation strategies.
- Use `--optimize-runs=1` when deployment cost matters more than long-term execution, and a large run count (hundreds or thousands) for high-volume transaction flows.
- Remember that optimizer settings also affect inline assembly and Yul IR transformations when the corresponding optimizer components are enabled.

## Managing Imports

- The compiler automatically resolves relative imports from the filesystem.
- Remap import prefixes with `prefix=path`, e.g. `solc github.com/ethereum/dapp-bin/=/usr/local/lib/dapp-bin/ file.sol`.
- Use `--base-path`, `--include-path`, and `--allow-paths` to control which directories `solc` may read for sources and dependencies. Paths provided on the command line are implicitly trusted.
- Any directory supplied via `--base-path` is always accessible. Other folders need to be explicitly granted via `--allow-paths=/path/one,/path/two`.
- Import paths that do not start with `./` or `../` resolve relative to the base and include paths, and the injected prefix is stripped from contract metadata.
- For multi-project workspaces, maintain a remapping file and pass it through `--remapfile` or include the mappings in the `remappings` array of the standard JSON settings.

## Library Linking

- Unlinked bytecode contains placeholders such as `__$53aea86b7d70b31448b230b20ae141a537$__` that reference fully qualified library names.
- Supply concrete addresses with `--libraries "file.sol:Math=0x1234..."` or by passing a file that lists mappings (one per line).
- Prefer linking during compilation so that the contract metadata remains consistent.
- The placeholder derives from the keccak256 hash of the fully qualified library name (source path + library symbol).
- `solc --link` accepts unlinked hex binaries and performs in-place substitution, but does **not** refresh the metadata hash. Use it sparingly and only when you understand the metadata implications.
- As of Solidity 0.8.1, `=` is the preferred delimiter between library and address (`file.sol:Math=0x...`). The legacy `:` separator remains accepted for backward compatibility but will be removed.

## Choosing an EVM Target

- Set the target hard fork with `--evm-version <version>`. Supported identifiers range from historical forks (e.g. `homestead`, `byzantium`) to the newest releases (`prague`, `osaka`).
- Targeting the correct fork ensures opcodes, gas costs, and available language features match the chain environment.
- The flag is available in both CLI (`--evm-version cancun`) and standard JSON mode (`"settings": { "evmVersion": "cancun" }`).
- Incorrect targets can break deployed contracts on custom chains, so align the compiler fork with the runtime EVM configuration before deployment.

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
- **prague** *(default)*: targets the latest post-Cancun improvements; verify downstream tooling supports it before opting in.

## JSON Compiler Interface

- The preferred automation path is `solc --standard-json`, which reads JSON from stdin and returns JSON on stdout.
- Inputs must specify the language (`"Solidity"`, `"Yul"`, etc.), a `sources` mapping, and optional `settings` (optimizer, remappings, EVM version, EOF version).
- Outputs include compiled artifacts, diagnostics, and metadata. The process exit code is always zero; rely on the JSON payload for error reporting.
- In JSON mode, `--base-path` still controls which directories are readable; the compiler refuses to read outside of those scopes unless the path is explicitly allowed.
- Provide library addresses via the `libraries` object inside the JSON input to ensure metadata consistency during automated builds.

Use this document alongside the upstream Solidity documentation when configuring build scripts or CI jobs.
