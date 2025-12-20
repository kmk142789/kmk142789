import glob
import json
import sys
from pathlib import Path

from jsonschema import validate

CASE_SCHEMA_PATH = Path("schemas/case.schema.json")
OUTCOME_SCHEMA_PATH = Path("schemas/case_outcome.schema.json")
CASE_DATA_GLOB = "data/cases/*.json"
OUTCOME_LEDGER_PATH = Path("ledger/case_outcomes.jsonl")


def load_schema(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_cases(case_schema: dict) -> set[str]:
    case_ids: set[str] = set()
    ok = True
    for case_file in glob.glob(CASE_DATA_GLOB):
        with open(case_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        try:
            validate(payload, case_schema)
            case_ids.add(payload.get("case_id"))
        except Exception as exc:
            ok = False
            print(f"ERROR {case_file}: {exc}")
    if not ok:
        sys.exit(1)
    return case_ids


def validate_outcomes(outcome_schema: dict, case_ids: set[str]) -> None:
    if not OUTCOME_LEDGER_PATH.exists():
        print("No outcomes ledger found; skipping")
        return

    ok = True
    with OUTCOME_LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                validate(payload, outcome_schema)
                if case_ids and payload.get("case_id") not in case_ids:
                    raise ValueError(
                        f"case_id {payload.get('case_id')} not found in data/cases"
                    )
            except Exception as exc:
                ok = False
                print(f"ERROR {OUTCOME_LEDGER_PATH}:{line_number}: {exc}")
    if not ok:
        sys.exit(1)


def main() -> None:
    case_schema = load_schema(CASE_SCHEMA_PATH)
    outcome_schema = load_schema(OUTCOME_SCHEMA_PATH)
    case_ids = validate_cases(case_schema)
    validate_outcomes(outcome_schema, case_ids)


if __name__ == "__main__":
    main()
