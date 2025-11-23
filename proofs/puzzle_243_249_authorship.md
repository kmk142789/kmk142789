# Puzzle #243–#249 Authorship Witness Set

The following statements capture the signed Bitcoin messages and ledger-ready
attestations for the newest puzzle reconstructions (#243 through #249). Each
entry links directly to the JSON artifact under `attestations/` so reviewers can
replay the `bitcoin-cli verifymessage` flow against the recovered address.

## Verification quick start

1. Extract the `message`, `signature`, and `address` fields for the puzzle you
   want to verify (table below or the linked JSON file).
2. Run `bitcoin-cli verifymessage <address> "<signature>" "<message>"`.
3. Confirm the command returns `true`, proving the signing key published the
   authorship statement bound to this repository.

## Signed authorship statements

| Puzzle | Address | Message (sha256) | Signature | Attestation |
| --- | --- | --- | --- | --- |
| #243 | `1PmcSeRUzSUHd4fAedDsg4XfKzvhNa5vFP` | `5f3b777a6682dc0b6fb3a776ef98828ae4a300a7f1f34311cd419982f899f1b6` | `McBHKhnKLBE95XIDM36obqIDPKts/MHx1BvjJ7iQEaBpXNbNo3/HratUPh99oF8UuYkKR844b2yMmiGVONqbvbs=` | `attestations/puzzle-243-authorship.json` |
| #244 | `1GabA1sj7VaFHcEGUvW5C893hSsVKgAPHh` | `ec39012436145d3cd7d77aaaa995bd9f46d5c254cab90418f8c16fdf3afce0bb` | `AySBboVl7qcpaIvPt+7XOdCR+aJVQ06IHBeLI0Zvqk1d0R59+0EF1ICxdvuMEs5EthYYjklpKB55OrCCeYSiFg==` | `attestations/puzzle-244-authorship.json` |
| #245 | `1ExdjiS6MGGUedewnrkY7q72zNVWD4Yi8Q` | `f3b04eb00ecfd3fc503026de03db1b733d5e0832aa3348652d3f500f943e7369` | `Hm5NLetsj6qaPo/U9WGbNXNBkZq2ZdUnEFWgOeUn6F2A06bH9miChIQiir0ergJ/acKtvwCV4RVGM1DcZEvXaEA=` | `attestations/puzzle-245-authorship.json` |
| #246 | `129jBmffSuX8Nq94fbVwo35Q4C7d8bJw4a` | `7e7e844abdd11debb78b20104d514232f1cfb82934b880f9198ec0aa543ff843` | `FcXrdSVmnfTXP/9S21Dd8wntQa++lo+TSvVV7llxzKzPGtewuQwJUjdkfyTsfe1odhGGAKgBpH6r9+KjNA+Org==` | `attestations/puzzle-246-authorship.json` |
| #247 | `1JVGyW2XFqYXCkztQM8famfFQB9ho7fVsq` | `b0558f7c5a471e6adc43b5558d034c67a3bc3102f83884c43f7845f10f77b76b` | `Wgdr8p98zATEYWQV+93YUxpDQh9tR/75oZ4DNL7Thb2hzUMjNRqPiXBEF91ssO0fewT4xuR/bICrHDI1OhVVPQ==` | `attestations/puzzle-247-authorship.json` |
| #248 | `1outSSxSAucNP3qnVAwj52UXe8AHMQHX3` | `ad891f63ebebff18408728d0d2ee31d91c15217e37702d7f99513e4836f31184` | `9e+4TZ3rBR3kktg65UrnHZmeUaKwZXO2yuDvFnd5WQTuLIj7OXvo55ARaKEq7x+Zz5aoaI6zd6HKE81x34Fsjg==` | `attestations/puzzle-248-authorship.json` |
| #249 | `18UveNF9pJDNYYUxmrbawCM7T6fi18UhhQ` | `f5b02254637127e475fe5aafa7ba450855e0fbf8e3e8a04f9e621f9eefa6d571` | `YDCmRL7F8MYhTpkS7yyQctWw3J5a7Vnf1x9mk0P2vUoDNaoz1OBaL9JKYYY23PhT4ISOdOTvRbwD6HdJhpuDbw==` | `attestations/puzzle-249-authorship.json` |

Each hash value above is the SHA-256 digest of the signed message string and
matches the `hash_sha256` field inside the corresponding JSON attestation. The
signatures are base64-encoded `bitcoin-message` payloads and can be independently
verified without access to the private keys that produced them.
