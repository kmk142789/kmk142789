import sys

PATHS = {
  "glyph_cloud/": "track:glyph-cloud",
  "verifier/": "track:continuum",
  "api/": "track:continuum",
  "federated_pulse/": "track:federated-pulse",
  "telemetry/": "track:memory-store",
  ".github/": "track:opencode",
  "wallet_attest/": "track:wallets",
}

def main():
    for p, label in PATHS.items():
        if any(arg.startswith(p) for arg in sys.argv[1:]):
            print(label)
            return
    print("other")


if __name__ == "__main__":
    main()
