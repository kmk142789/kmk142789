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
