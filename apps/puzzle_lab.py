"""Streamlit dashboard for exploring ``echo_map.json`` puzzle records."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from echo_puzzle_lab import (
    build_dataframe,
    export_records,
    fetch_ud_metadata,
    has_ud_credentials,
    load_records,
    save_records,
    update_ud_records,
)
from echo_puzzle_lab.charts import save_charts

st.set_page_config(page_title="Puzzle Lab", layout="wide")

REPORT_FIGURE_DIR = Path("reports") / "figures"
EXPORT_DIR = Path("exports")


@st.cache_data(show_spinner=False)
def load_dataset() -> tuple[list, pd.DataFrame]:
    records = load_records()
    frame = build_dataframe(records)
    return records, frame


def _copy_button(label: str, text: str, *, key: str) -> None:
    payload = json.dumps(text)
    st.components.v1.html(
        f"""
        <button onclick="navigator.clipboard.writeText({payload});"
                style="margin-right:0.5rem; padding:0.4rem 0.8rem;">
            {label}
        </button>
        """,
        height=45,
    )


def _apply_filters(frame: pd.DataFrame) -> pd.DataFrame:
    filtered = frame.copy()

    families = sorted(filtered["Family"].dropna().unique().tolist())
    selected_families = st.sidebar.multiselect(
        "Script family", families, default=families
    )
    if selected_families:
        filtered = filtered[filtered["Family"].isin(selected_families)]

    ud_filter = st.sidebar.selectbox(
        "UD binding", ["All", "Bound", "Unbound"], index=0
    )
    if ud_filter == "Bound":
        filtered = filtered[filtered["UD_Bound"]]
    elif ud_filter == "Unbound":
        filtered = filtered[~filtered["UD_Bound"]]

    mismatch_filter = st.sidebar.selectbox(
        "Mismatch status", ["All", "Matching", "Only mismatches"], index=0
    )
    if mismatch_filter == "Matching":
        filtered = filtered[~filtered["Mismatch"]]
    elif mismatch_filter == "Only mismatches":
        filtered = filtered[filtered["Mismatch"]]

    if not filtered.empty:
        min_date = filtered["Updated"].min().date()
        max_date = filtered["Updated"].max().date()
        start_date, end_date = st.sidebar.date_input(
            "Updated between",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        mask = filtered["Updated"].dt.date.between(start_date, end_date)
        filtered = filtered[mask]

    search = st.sidebar.text_input(
        "Search", placeholder="Puzzle, address, hash160..."
    ).strip()
    if search:
        search_lower = search.lower()
        filtered = filtered[
            filtered.apply(
                lambda row: search_lower in str(row["Puzzle"]).lower()
                or search_lower in str(row["Address"]).lower()
                or search_lower in str(row["Hash160"]).lower(),
                axis=1,
            )
        ]

    return filtered


def _render_summary(frame: pd.DataFrame) -> None:
    total = len(frame)
    bound = int(frame["UD_Bound"].sum()) if not frame.empty else 0
    mismatch = int(frame["Mismatch"].sum()) if not frame.empty else 0
    st.metric("Visible puzzles", total)
    st.metric("UD bound", bound)
    st.metric("Mismatches", mismatch)


def _status_label(row: pd.Series) -> str:
    if row["Mismatch"]:
        return "Mismatch"
    if not row["Tested"]:
        return "Untested"
    return "OK"


def _render_table(frame: pd.DataFrame) -> tuple[pd.DataFrame, int | None]:
    display = frame.copy()
    if display.empty:
        st.info("No puzzles match the current filters.")
        return display, None

    display["Hash160"] = display["Hash160_8"]
    display["UD"] = display["UD_Count"]
    display["PR"] = display["Lineage_PR"]
    display["Status"] = display.apply(_status_label, axis=1)
    display = display[["Puzzle", "Address", "Family", "Hash160", "UD", "PR", "Status"]]

    selection_index = st.session_state.get("selected_puzzle_index", 0)
    selection_index = min(selection_index, len(display) - 1)

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        height=420,
    )

    puzzle_ids = display["Puzzle"].tolist()
    if not puzzle_ids:
        return display, None

    selected_puzzle = st.selectbox(
        "Detail view", puzzle_ids, index=selection_index
    )
    st.session_state["selected_puzzle_index"] = puzzle_ids.index(selected_puzzle)
    return display, selected_puzzle


def _render_detail(records: list, puzzle_id: int | None) -> None:
    if puzzle_id is None:
        return

    record_lookup = {record.puzzle: record for record in records}
    record = record_lookup.get(puzzle_id)
    if not record:
        st.warning("Selected puzzle not found in the loaded dataset.")
        return

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader(f"Puzzle #{record.puzzle}")
        st.code(record.pkscript.asm, language="asm")
        st.caption("pkScript ASM")
        _copy_button("Copy ASM", record.pkscript.asm, key=f"copy-asm-{record.puzzle}")
        st.code(record.pkscript.hex, language="text")
        st.caption("pkScript hex")
        _copy_button("Copy hex", record.pkscript.hex, key=f"copy-hex-{record.puzzle}")

        reconstruction = getattr(record, "reconstruction", None)
        if reconstruction:
            st.markdown("### Reconstruction notes")
            notes = json.dumps(reconstruction, indent=2)
            st.code(notes, language="json")

    with col_right:
        st.markdown("### UD metadata")
        st.json(record.ud.model_dump(mode="json"))
        st.markdown("### Lineage")
        st.write(
            f"Commit: {record.lineage.commit or 'n/a'}\n\n"
            f"PR: {record.lineage.pr or 'n/a'}"
        )
        if record.lineage.source_files:
            st.markdown("### Sources")
            for source in record.lineage.source_files:
                st.page_link(source, label=source, icon="📄")

    st.markdown("---")

    selected_records = [record]
    if st.button("Re-verify selection", type="primary"):
        verify_df = build_dataframe(selected_records)
        mismatches = verify_df[verify_df["Mismatch"]]
        if mismatches.empty:
            st.success("Derived address matches stored value.")
        else:
            row = mismatches.iloc[0]
            st.error(
                f"Mismatch detected. Stored {row['Address']} vs derived {row['Derived']}."
            )

    if st.button("Export view", key=f"export-{record.puzzle}"):
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        destination = EXPORT_DIR / f"puzzle_lab_{record.puzzle}_{timestamp}.jsonl"
        export_records(selected_records, destination)
        st.success(f"Exported puzzle to {destination}")


def _ud_banner() -> None:
    if has_ud_credentials():
        st.sidebar.success("UD credentials detected. Enable enrichment from the actions panel.")
    else:
        st.sidebar.info(
            "UD credentials not configured (set UD_API_KEY or UD_JWT). "
            "The dashboard remains fully functional."
        )


def _enrich_button(records: list, frame: pd.DataFrame) -> None:
    if not has_ud_credentials():
        return

    if st.button("Fetch UD for visible rows"):
        addresses = frame["Address"].tolist()
        metadata = fetch_ud_metadata(addresses)
        if not metadata:
            st.warning("No UD metadata retrieved.")
            return
        updated = update_ud_records(records, metadata)
        save_records(updated)
        load_dataset.clear()
        st.success(f"Updated UD metadata for {len(metadata)} puzzles.")
        st.experimental_rerun()


def _share_deep_link(filters: dict[str, str]) -> None:
    st.sidebar.markdown("### Share deep link")
    st.sidebar.button(
        "Generate link",
        on_click=lambda: st.experimental_set_query_params(**filters),
    )
    params = st.experimental_get_query_params()
    if params:
        encoded = "&".join(f"{k}={'/'.join(v)}" for k, v in params.items())
        st.sidebar.code(f"?{encoded}")


def main() -> None:
    st.title("Puzzle Lab")
    st.caption("Explore, verify, and enrich puzzle reconstructions from echo_map.json")

    records, frame = load_dataset()
    _ud_banner()

    filtered = _apply_filters(frame)

    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    with metrics_col1:
        st.metric("Total puzzles", len(frame))
    with metrics_col2:
        st.metric("Visible", len(filtered))
    with metrics_col3:
        st.metric("UD bound", int(filtered["UD_Bound"].sum()) if not filtered.empty else 0)

    _render_summary(filtered)

    save_charts(frame, REPORT_FIGURE_DIR)

    display_df, selected_puzzle = _render_table(filtered)
    _enrich_button(records, filtered)
    _share_deep_link({"puzzle": [str(selected_puzzle)]} if selected_puzzle else {})
    _render_detail(records, selected_puzzle)


if __name__ == "__main__":
    main()
