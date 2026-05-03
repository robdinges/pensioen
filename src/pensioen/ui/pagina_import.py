"""Streamlit-pagina: importeer MijnPensioenoverzicht-bestanden voor beide personen."""

from __future__ import annotations

import io
from datetime import date

import streamlit as st

from pensioen.models.pensioen_record import PensioenRecord
from pensioen.parsers.parser_mpo import MPOParser
from pensioen.validators.validator import valideer_records
from pensioen.ui.sessie_persistentie import sla_sessie_op


def _toon_validatiemeldingen(resultaat) -> None:
    for fout in resultaat.fouten:
        st.error(f"**FOUT** [{fout.veld}]: {fout.bericht}")

    duplicate_warnings = [
        warn
        for warn in resultaat.waarschuwingen
        if warn.veld == "regeling" and "Duplicaat gevonden" in warn.bericht
    ]
    overige_waarschuwingen = [
        warn
        for warn in resultaat.waarschuwingen
        if warn not in duplicate_warnings
    ]

    for warn in overige_waarschuwingen:
        st.warning(f"**WAARSCHUWING** [{warn.veld}]: {warn.bericht}")

    if duplicate_warnings:
        st.warning(
            "**WAARSCHUWING** [regeling]: Er zijn mogelijke duplicaten gevonden. "
            "Controleer het detail-log als u dit wilt nalopen."
        )
        with st.expander("Bekijk detail-log duplicaten"):
            for warn in duplicate_warnings:
                st.write(f"- {warn.bericht}")

    for info in resultaat.info:
        st.info(f"**INFO**: {info.bericht}")


def toon_import_pagina() -> None:
    """Streamlit-pagina voor het importeren van pensioengegevens."""
    st.header("📂 Pensioengegevens importeren")
    st.write(
        "Upload uw MijnPensioenoverzicht-export (CSV, Excel of JSON). "
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
            type=["csv", "xlsx", "xls", "json"],
            key="upload_p1",
        )
        if bestand1 is not None:
            try:
                _p1 = st.session_state.get("persoon1")
                geboortedatum1 = (
                    _p1.geboortedatum if _p1 else st.session_state.get("geboortedatum_p1")
                )
                records1 = _parse_upload(bestand1, peildatum, geboortedatum1)
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
                    sla_sessie_op()
            except Exception as exc:
                st.error(f"Fout bij inlezen: {exc}")

    # --- Persoon 2 ---
    with col2:
        st.subheader("Persoon 2 (optioneel)")
        bestand2 = st.file_uploader(
            "MPO-bestand persoon 2",
            type=["csv", "xlsx", "xls", "json"],
            key="upload_p2",
        )
        if bestand2 is not None:
            try:
                _p2 = st.session_state.get("persoon2")
                geboortedatum2 = (
                    _p2.geboortedatum if _p2 else st.session_state.get("geboortedatum_p2")
                )
                records2 = _parse_upload(bestand2, peildatum, geboortedatum2)
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
                    sla_sessie_op()
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
    geboortedatum: date | None = None,
) -> list[PensioenRecord]:
    """Verwerk een geüpload bestand naar pensioenrecords."""
    import os
    import tempfile

    naam = bestand.name.lower()
    inhoud = bestand.read()

    if naam.endswith(".csv"):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(inhoud)
            tmp_pad = tmp.name
        try:
            records = MPOParser.parse_csv(tmp_pad, peildatum)
        finally:
            os.unlink(tmp_pad)
    elif naam.endswith((".xlsx", ".xls")):
        suffix = ".xlsx" if naam.endswith(".xlsx") else ".xls"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(inhoud)
            tmp_pad = tmp.name
        try:
            records = MPOParser.parse_excel(tmp_pad, peildatum)
        finally:
            os.unlink(tmp_pad)
    elif naam.endswith(".json"):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp.write(inhoud)
            tmp_pad = tmp.name
        try:
            records = MPOParser.parse_json(tmp_pad, peildatum, geboortedatum)
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
