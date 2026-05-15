"""Streamlit-pagina: belastingtarieven per jaar inzien en aanpassen."""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

import streamlit as st

from pensioen.models.scenario import TariefPeriodeItem
from pensioen.tax.belasting_loader import (
    beschikbare_jaren,
    config_naar_tariefwaarden,
    laad_tarieven,
    resolve_tariefwaarden_voor_jaar,
)
from pensioen.ui.scenario_context import get_actief_scenario
from pensioen.ui.sessie_persistentie import sla_sessie_op
from pensioen.ui.helpers import fmt_eur, fmt_pct, toon_gap_badge


def toon_instellingen_pagina() -> None:
    """Streamlit-pagina voor het inzien en overschrijven van belastingtarieven."""
    st.header("Instellingen")

    # ─── Tariefstatus over prognosehorizon ───────────────────────────────────
    st.subheader("Tariefstatus")
    beschikbaar = beschikbare_jaren()
    jaar_van_prognose = st.session_state.get("jaar_van", 2025)
    jaar_tot_prognose = st.session_state.get("jaar_tot", 2045)

    if beschikbaar:
        jaren_bereik = range(int(jaar_van_prognose), int(jaar_tot_prognose) + 1)
        ontbrekend = [j for j in jaren_bereik if j not in beschikbaar]
        toon_gap_badge(ontbrekend)

        with st.expander(f"Beschikbare tariefbestanden ({len(beschikbaar)} jaar)"):
            cols = st.columns(min(len(beschikbaar), 6))
            for i, j in enumerate(sorted(beschikbaar)):
                cols[i % len(cols)].success(f"✅ {j}")
            if ontbrekend:
                st.caption(
                    f"⚠️ Jaren zonder eigen tarieven ({len(ontbrekend)}): "
                    + ", ".join(str(j) for j in sorted(set(ontbrekend)))
                )
    else:
        st.error("❌ Geen tariefbestanden gevonden in de config-map.")

    st.divider()

    # ─── Tarieven bekijken per jaar ───────────────────────────────────────────
    st.subheader("Belastingtarieven per jaar")
    jaar_opties = sorted(beschikbaar) if beschikbaar else [2025, 2026]
    jaar = st.selectbox("Jaar", jaar_opties, key="tarieven_jaar_select")

    config, melding = laad_tarieven(jaar)
    if melding:
        st.warning(f"⚠️ {melding}")

    # Box 1 schijven — tabel in plaats van losse tekst
    st.markdown(f"**Box 1 – Niet-AOW (schijven voor {jaar})**")
    schijf_rijen = []
    for i, schijf in enumerate(config.box1_niet_aow, 1):
        tot_str = fmt_eur(schijf.tot) if schijf.tot else "daarboven"
        schijf_rijen.append({"Schijf": i, "Tarief": fmt_pct(schijf.tarief), "Tot": tot_str})
    if schijf_rijen:
        st.dataframe(pd.DataFrame(schijf_rijen), hide_index=True, use_container_width=False)

    st.markdown("**Box 1 – AOW-gerechtigd (schijf 1)**")
    st.write(f"  Schijf 1: {fmt_pct(config.box1_aow[0].tarief)}")

    # Heffingskortingen
    st.divider()
    st.markdown("**Heffingskortingen**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("AHK max", fmt_eur(config.ahk.max_bedrag))
        st.caption(
            f"Afbouw vanaf {fmt_eur(config.ahk.afbouw_inkomen_van)}, "
            f"{fmt_pct(config.ahk.afbouw_pct)} p.j."
        )
    with col2:
        st.metric("Arbeidskorting max", fmt_eur(config.arbeidskorting.max_bedrag))
        st.caption(
            f"Afbouw vanaf {fmt_eur(config.arbeidskorting.afbouw_drempel)}, "
            f"{fmt_pct(config.arbeidskorting.afbouw_pct)} p.j."
        )
    with col3:
        st.metric("Ouderenkorting max", fmt_eur(config.ouderenkorting.max_bedrag))
        st.caption(
            f"Afbouw vanaf {fmt_eur(config.ouderenkorting.afbouw_inkomen_van)}, "
            f"{fmt_pct(config.ouderenkorting.afbouw_pct)} p.j."
        )

    # Box 3
    st.divider()
    st.subheader("Box 3")
    col_b3a, col_b3b, col_b3c = st.columns(3)
    with col_b3a:
        st.metric("Vrijstelling p.p.", fmt_eur(config.box3.vrijstelling_per_persoon))
    with col_b3b:
        st.metric("Belastingtarief", fmt_pct(config.box3.tarief, 0))
    with col_b3c:
        st.metric(
            "Forfait spaargeld / beleggingen",
            f"{fmt_pct(config.box3.forfaitair_spaargeld)} / {fmt_pct(config.box3.forfaitair_overig)}",
        )
    st.caption(f"ℹ️ {config.box3.disclaimer}")

    # AOW-bedragen
    st.divider()
    st.subheader("AOW-bedragen")
    col4, col5 = st.columns(2)
    with col4:
        st.metric("Alleenstaand (p/m)", fmt_eur(config.aow_bedrag.alleenstaande_per_maand))
    with col5:
        st.metric("Gehuwd/samenwonend (p/m)", fmt_eur(config.aow_bedrag.gehuwd_of_samenwonend_per_maand))

    st.caption(
        "ℹ️ Tarieven worden ingelezen uit `config/belasting_YYYY.json`. "
        "Voor onbekende jaren wordt het meest recente beschikbare jaar gebruikt als aanname."
    )

    # ─── Periodegebaseerde tariefoverrides ──────────────────────────────────
    st.divider()
    st.subheader("Tariefperiodes per scenario")
    scenario_lijst = st.session_state.get("scenario_lijst", [])
    actief_scenario = get_actief_scenario(scenario_lijst)
    if actief_scenario is None:
        st.warning("Geen actief scenario beschikbaar voor tariefbeheer.")
    else:
        st.caption(
            f"Actief scenario: {actief_scenario.naam}. "
            "Bij overlap geldt de laatst opgegeven regel; bij hiaat loopt de laatst geldende waarde door."
        )

        basis_waarden = config_naar_tariefwaarden(config)
        sleutel_opties = sorted(basis_waarden.keys())
        gekozen_sleutel = st.selectbox(
            "Tarief om te beheren",
            options=sleutel_opties,
            key="tarief_periode_sleutel",
        )

        bestaande = [
            p for p in actief_scenario.tarief_periodes
            if p.sleutel == gekozen_sleutel
        ]
        periode_df = pd.DataFrame([
            {
                "startjaar": p.startjaar,
                "eindjaar": p.eindjaar,
                "waarde": float(p.waarde),
                "inflatie_pct": float(p.inflatie_pct),
            }
            for p in bestaande
        ]) if bestaande else pd.DataFrame(
            columns=["startjaar", "eindjaar", "waarde", "inflatie_pct"]
        )

        periode_editor = st.data_editor(
            periode_df,
            num_rows="dynamic",
            column_config={
                "startjaar": st.column_config.NumberColumn("Beginjaar (leeg = vanaf begin)", step=1),
                "eindjaar": st.column_config.NumberColumn("Eindjaar (leeg = tot einde)", step=1),
                "waarde": st.column_config.NumberColumn("Waarde", step=0.0001, format="%.6f"),
                "inflatie_pct": st.column_config.NumberColumn("Inflatie %", step=0.1, format="%.2f"),
            },
            key="tarief_periode_editor",
            use_container_width=True,
        )

        if st.button("Periode-regels opslaan", key="tarief_periode_opslaan"):
            nieuw: list[TariefPeriodeItem] = []
            for _, rij in periode_editor.iterrows():
                if pd.isna(rij.get("waarde")):
                    continue
                start_raw = rij.get("startjaar")
                eind_raw = rij.get("eindjaar")
                nieuw.append(
                    TariefPeriodeItem(
                        sleutel=gekozen_sleutel,
                        startjaar=int(start_raw) if pd.notna(start_raw) else None,
                        eindjaar=int(eind_raw) if pd.notna(eind_raw) else None,
                        waarde=rij.get("waarde"),
                        inflatie_pct=rij.get("inflatie_pct") if pd.notna(rij.get("inflatie_pct")) else 0,
                    )
                )

            overige = [p for p in actief_scenario.tarief_periodes if p.sleutel != gekozen_sleutel]
            actief_scenario.tarief_periodes = overige + nieuw
            actief_scenario.laatst_gewijzigd_op = datetime.now()

            for i, sc in enumerate(scenario_lijst):
                if sc.naam == actief_scenario.naam:
                    scenario_lijst[i] = actief_scenario
                    break
            st.session_state["scenario_lijst"] = scenario_lijst
            sla_sessie_op()
            st.success("Tariefperiode-regels opgeslagen.")
            st.rerun()

        jaar_van = int(st.session_state.get("jaar_van", jaar))
        jaar_tot = int(st.session_state.get("jaar_tot", jaar + 20))
        tijdlijn = []
        for y in range(jaar_van, jaar_tot + 1):
            cfg_y, _ = laad_tarieven(y)
            cfg_resolved, bronnen = resolve_tariefwaarden_voor_jaar(
                cfg_y,
                y,
                actief_scenario.tarief_periodes,
            )
            waarde_y = config_naar_tariefwaarden(cfg_resolved).get(gekozen_sleutel, basis_waarden[gekozen_sleutel])
            tijdlijn.append({
                "Jaar": y,
                "Waarde": float(waarde_y),
                "Bron": bronnen.get(gekozen_sleutel, "basisconfig"),
            })
        st.markdown("**Tijdlijn (jaarlijks)**")
        st.dataframe(pd.DataFrame(tijdlijn), hide_index=True, use_container_width=True)

    # ─── Tariefgenerator ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("Nieuw tariefbestand genereren")
    st.caption(
        "Vul hieronder de tarieven in voor een nieuw jaar en download het gegenereerde JSON-bestand. "
        "Sla het op als `config/belasting_YYYY.json` en herstart de applicatie om het te activeren."
    )

    jaar_opties_gen = sorted(beschikbaar) if beschikbaar else [2025, 2026]
    basisjaar_gen = st.selectbox(
        "Basisjaar (start met waarden van dit jaar)",
        options=jaar_opties_gen,
        index=len(jaar_opties_gen) - 1,
        key="tariefgen_basisjaar",
    )
    doeljaar_gen = st.number_input(
        "Nieuw jaar", min_value=2024, max_value=2100,
        value=max(jaar_opties_gen) + 1,
        step=1, key="tariefgen_doeljaar",
    )

    basis_cfg, _ = laad_tarieven(basisjaar_gen)

    with st.form("tariefgen_formulier"):
        st.markdown("**Box 1 – niet-AOW (schijven)**")
        gen_schijven_niet_aow = []
        for i, s in enumerate(basis_cfg.box1_niet_aow):
            c1, c2 = st.columns(2)
            with c1:
                tot_val = st.number_input(
                    f"Schijf {i+1} — bovengrens (0 = geen grens)",
                    value=float(s.tot) if s.tot else 0.0,
                    step=100.0, key=f"gen_s1_tot_{i}",
                )
            with c2:
                tar_val = st.number_input(
                    f"Schijf {i+1} — tarief (bijv. 0.3693)",
                    value=float(s.tarief), step=0.001, format="%.4f",
                    key=f"gen_s1_tar_{i}",
                )
            gen_schijven_niet_aow.append({"tot": tot_val if tot_val > 0 else None, "tarief": tar_val})

        st.markdown("**Box 1 – AOW-gerechtigd (schijven)**")
        gen_schijven_aow = []
        for i, s in enumerate(basis_cfg.box1_aow):
            c1, c2 = st.columns(2)
            with c1:
                tot_val = st.number_input(
                    f"AOW-schijf {i+1} — bovengrens (0 = geen grens)",
                    value=float(s.tot) if s.tot else 0.0,
                    step=100.0, key=f"gen_s2_tot_{i}",
                )
            with c2:
                tar_val = st.number_input(
                    f"AOW-schijf {i+1} — tarief",
                    value=float(s.tarief), step=0.001, format="%.4f",
                    key=f"gen_s2_tar_{i}",
                )
            gen_schijven_aow.append({"tot": tot_val if tot_val > 0 else None, "tarief": tar_val})

        st.markdown("**Algemene heffingskorting**")
        c1, c2, c3, c4 = st.columns(4)
        ahk_max = c1.number_input("Max (€)", value=float(basis_cfg.ahk.max_bedrag), step=10.0, key="gen_ahk_max")
        ahk_van = c2.number_input("Afbouw vanaf (€)", value=float(basis_cfg.ahk.afbouw_inkomen_van), step=100.0, key="gen_ahk_van")
        ahk_pct = c3.number_input("Afbouw % (bijv. 0.06)", value=float(basis_cfg.ahk.afbouw_pct), step=0.001, format="%.4f", key="gen_ahk_pct")
        ahk_min = c4.number_input("Minimum (€)", value=float(basis_cfg.ahk.minimum), step=1.0, key="gen_ahk_min")

        st.markdown("**Arbeidskorting**")
        c1, c2, c3, c4 = st.columns(4)
        ak_max = c1.number_input("Max (€)", value=float(basis_cfg.arbeidskorting.max_bedrag), step=10.0, key="gen_ak_max")
        ak_drempel = c2.number_input("Afbouw drempel (€)", value=float(basis_cfg.arbeidskorting.afbouw_drempel), step=100.0, key="gen_ak_drempel")
        ak_pct = c3.number_input("Afbouw %", value=float(basis_cfg.arbeidskorting.afbouw_pct), step=0.001, format="%.4f", key="gen_ak_pct")
        ak_min = c4.number_input("Minimum (€)", value=float(basis_cfg.arbeidskorting.minimum), step=1.0, key="gen_ak_min")

        st.markdown("**Ouderenkorting**")
        c1, c2, c3, c4 = st.columns(4)
        ok_max = c1.number_input("Max (€)", value=float(basis_cfg.ouderenkorting.max_bedrag), step=10.0, key="gen_ok_max")
        ok_van = c2.number_input("Afbouw vanaf (€)", value=float(basis_cfg.ouderenkorting.afbouw_inkomen_van), step=100.0, key="gen_ok_van")
        ok_pct = c3.number_input("Afbouw %", value=float(basis_cfg.ouderenkorting.afbouw_pct), step=0.001, format="%.4f", key="gen_ok_pct")
        ok_min = c4.number_input("Minimum (€)", value=float(basis_cfg.ouderenkorting.minimum), step=1.0, key="gen_ok_min")

        st.markdown("**Box 3**")
        c1, c2, c3, c4 = st.columns(4)
        b3_vrijstelling = c1.number_input("Vrijstelling p.p. (€)", value=float(basis_cfg.box3.vrijstelling_per_persoon), step=100.0, key="gen_b3_vrijstelling")
        b3_tarief = c2.number_input("Tarief (bijv. 0.36)", value=float(basis_cfg.box3.tarief), step=0.01, format="%.4f", key="gen_b3_tarief")
        b3_spaar = c3.number_input("Forfait spaargeld", value=float(basis_cfg.box3.forfaitair_spaargeld), step=0.001, format="%.4f", key="gen_b3_spaar")
        b3_overig = c4.number_input("Forfait overig", value=float(basis_cfg.box3.forfaitair_overig), step=0.001, format="%.4f", key="gen_b3_overig")

        st.markdown("**AOW-bedragen**")
        c1, c2 = st.columns(2)
        aow_alleen = c1.number_input("Alleenstaand p/m (€)", value=float(basis_cfg.aow_bedrag.alleenstaande_per_maand), step=10.0, key="gen_aow_alleen")
        aow_samen = c2.number_input("Gehuwd/samenwonend p/m (€)", value=float(basis_cfg.aow_bedrag.gehuwd_of_samenwonend_per_maand), step=10.0, key="gen_aow_samen")

        genereer = st.form_submit_button("📋 Genereer JSON-bestand")

    if genereer:
        tarieven_data = {
            "_toelichting": f"Belastingtarieven {int(doeljaar_gen)} — gegenereerd via pensioenplanner op basis van {basisjaar_gen}",
            "_bron": "Handmatig gegenereerd",
            "jaar": int(doeljaar_gen),
            "box1_niet_aow": {"schijven": gen_schijven_niet_aow},
            "box1_aow": {"schijven": gen_schijven_aow},
            "algemene_heffingskorting": {
                "max": ahk_max,
                "afbouw_inkomen_van": ahk_van,
                "afbouw_pct": ahk_pct,
                "minimum": ahk_min,
            },
            "arbeidskorting": {
                "max": ak_max,
                "afbouw_drempel": ak_drempel,
                "afbouw_pct": ak_pct,
                "minimum": ak_min,
            },
            "ouderenkorting": {
                "max": ok_max,
                "afbouw_inkomen_van": ok_van,
                "afbouw_pct": ok_pct,
                "minimum": ok_min,
            },
            "box3": {
                "vrijstelling_per_persoon": b3_vrijstelling,
                "tarief": b3_tarief,
                "forfaitair_spaargeld": b3_spaar,
                "forfaitair_overig": b3_overig,
                "_disclaimer": basis_cfg.box3.disclaimer,
            },
            "aow_bedrag": {
                "alleenstaande_per_maand": aow_alleen,
                "gehuwd_of_samenwonend_per_maand": aow_samen,
            },
        }
        json_bytes = json.dumps(tarieven_data, indent=2, ensure_ascii=False).encode("utf-8")
        bestandsnaam = f"belasting_{int(doeljaar_gen)}.json"
        st.download_button(
            label=f"⬇️ Download {bestandsnaam}",
            data=json_bytes,
            file_name=bestandsnaam,
            mime="application/json",
            key="tariefgen_download",
        )
        st.caption(
            f"Sla `{bestandsnaam}` op in de map `config/` van het project "
            "en herstart de applicatie om de nieuwe tarieven te activeren."
        )

