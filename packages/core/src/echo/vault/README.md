# Echo Vault (encrypted, searchable)

Initialize:

```bash
echo-vault init --path ./vault.db
```

Import from stdin:

```bash
echo-vault import --path ./vault.db --label "alpha" --fmt hex --tags lab,test --from-stdin
```

Find:

```bash
echo-vault find --path ./vault.db --q alpha --tags lab
```

Sign:

```bash
echo-vault sign --path ./vault.db <id> --hex "feedface" --repeat 5
```

Inspect packaged authority bindings:

```bash
echo-vault authority --json
```

Show an example authority binding entry to mirror for custom data files:

```bash
echo-vault authority --example
```
