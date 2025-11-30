import argparse
from atlas_os.bootstrap import bootstrap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--secret", required=True, help="master secret for vault/governance")
    args = parser.parse_args()

    results = bootstrap(args.secret)
    for sid, res in results.items():
        print(sid, "=>", res)


if __name__ == "__main__":
    main()
