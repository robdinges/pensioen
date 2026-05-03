"""Streamlit-pagina: importeer MijnPensioenoverzicht-bestanden voor beide personen."""

from __future__ import annotations

import io
from datetime import date

import streamlit as st

from pensioen.models.pensioen_record import PensioenRecord
from pensioen.parsers.parser_mpo import MPOParser
from pensioen.validators.validator import valideer_records


def _toon_validatiemeldingen(resultaat) -> None:
    for fout in resultaat.fouten:
        st.error(f"**FOUT** [{fout.veld}]: {fout.bericht}")
    for warn in resultaat.waarschuwingen:
        st.warning(f"**WAARSCHUWING** [{warn.veld}]: {warn.bericht}")
    for info in resultaat.info:
        st.info(f"**INFO**: {info.bericht}")


def toon_import_pagina() -> None:
    """Streamlit-pagina voor het importeren van pensioengegevens."""
    st.header("📂 Pensioengegevens importeren")
    st.write(
        "Upload uw MijnPensioenoverzicht-export (CSV of Excel). "
        "Indien u een partner heeft, upload ook diens bestand."
    )

    peildatum = st.date_input(
        "Peildatum voor de import",
        value=date.today(),
        help="Datum waarop de pensioenopgaven zijn opgesteld.",
    )

    col1, col2 = st.columns(2)

    # --- Persoon 1 ---
    with col1:
        st.subheader("Persoon 1")
        bestand1 = st.file_uploader(
            "MPO-bestand persoon 1",
            type=["csv", "xlsx", "xls"],
            key="upload_p1",
        )
        if bestand1 is not None:
            try:
                records1 = _parse_upload(bestand1, peildatum)
                validatie = valideer_records(records1)
                _toon_validatiemeldingen(validatie)
                if records1:
                    st.success(f"✅ {len(records1)} pensioenregel(s) geladen")
                    st.dataframe(
                        _naar_dataframe(records1),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.session_state["records_p1"] = records1
            except Exception as exc:
                st.error(f"Fout bij inlezen: {exc}")

    # --- Persoon 2 ---
    with col2:
        st.subheader("Persoon 2 (optioneel)")
        bestand2 = st.file_uploader(
            "MPO-bestand persoon 2",
            type=["csv", "xlsx", "xls"],
            key="upload_p2",
        )
        if bestand2 is not None:
            try:
                records2 = _parse_upload(bestand2, peildatum)
                validatie = valideer_records(records2)
                _toon_validatiemeldingen(validatie)
                if records2:
                    st.success(f"✅ {len(records2)} pensioenregel(s) geladen")
                    st.dataframe(
                        _naar_dataframe(records2),
                        use_container_width=True,
                        hide_index=True,
                    )
                    st.session_state["records_p2"] = records2
            except Exception as exc:
                st.error(f"Fout bij inlezen: {exc}")

    st.divider()
    totaal_p1 = len(st.session_state.get("records_p1", []))
    totaal_p2 = len(st.session_state.get("records_p2", []))
    st.caption(
        f"Geladen: {totaal_p1} record(s) persoon 1 | {totaal_p2} record(s) persoon 2"
    )


def _parse_upload(
    bestand: "st.runtime.uploaded_file_manager.UploadedFile",
    peildatum: date,
) -> list[PensioenRecord]:
    """Verwerk een geüpload bestand naar pensioenrecords."""
    naam = bestand.name.lower()
    inhoud = bestand.read()

    if naam.endswith(".csv"):
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(inhoud)
            tmp_pad = tmp.name
        try:
            records = MPOParser.parse_csv(tmp_pad, peildatum)
        finally:
            os.unlink(tmp_pad)
    elif naam.endswith((".xlsx", ".xls")):
        import tempfile, os
        suffix = ".xlsx" if naam.endswith(".xlsx") else ".xls"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(inhoud)
            tmp_pad = tmp.name
        try:
            records = MPOParser.parse_excel(tmp_pad, peildatum)
        finally:
            os.unlink(tmp_pad)
    else:
        raise ValueError(f"Onbekend bestandstype: {bestand.name}")

    return records


def _naar_dataframe(records: list[PensioenRecord]):
    """Converteer pensioenrecords naar een weergave-DataFrame."""
    import pandas as pd

    return pd.DataFrame(
        [
            {
                "Uitvoerder": r.uitvoerder,
                "Regeling": r.regeling,
                "Type": r.type_pensioen.value,
                "Ingangsdatum": r.ingangsdatum,
                "Bruto/jaar (€)": float(r.bruto_per_jaar),
                "Indexatie (%)": float(r.indexatie_verwacht_pct),
            }
            for r in records
        ]
    )
