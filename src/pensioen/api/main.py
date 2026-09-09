"""FastAPI entrypoint voor de pensioenrekenengine."""

from __future__ import annotations

from pensioen.calculations.actuariele_jaarvergelijking import bouw_actuariele_jaarvergelijking

import os
import tempfile
from pathlib import Path
from decimal import Decimal

from fastapi import FastAPI, HTTPException
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse, Response

from pensioen.api.referentietabellen import codes_en_labels, input_hints
from pensioen.api.schemas import BerekeningRequest, RapportageRequest, VergelijkingRequest, PensioenopbouwRequest, ActuarieleSchattingRequest
from pensioen.api.serialisatie import naar_json_compatibel
from pensioen.calculations.resultaat_service import bereken_resultaten
from pensioen.calculations.inheritance_engine import validate_inheritance_tree, resolve_scenario
from pensioen.calculations.actuariele_scenarios import bouw_actuariele_scenarios
from pensioen.calculations.pensioenopbouw_simulator import bouw_opbouwscenarios, bouw_opbouwuitkomst
from pensioen.parsers.parser_mpo import MPOParser
from pensioen.calculations.scenario_engine import vergelijk_scenarios
from pensioen.models.output_contract import OUTPUT_CONTRACT
from pensioen.reports.rapport_engine import genereer_rapport

app = FastAPI(
    title="Pensioenplanner API",
    version="1.0.0",
    description="Stateless API-laag bovenop de bestaande pensioenrekenengine.",
)


def _valideer_inheritance(scenario_lijst: list) -> None:
    waarschuwingen = validate_inheritance_tree(scenario_lijst)
    if waarschuwingen:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "inheritance_validation_error",
                "waarschuwingen": waarschuwingen,
            },
        )


@app.get("/api/v1/health")
def healthcheck() -> dict[str, str]:
    """Eenvoudige healthcheck endpoint."""
    return {"status": "ok"}


@app.get("/api/v1/referenties/codes")
def referenties_codes_endpoint() -> JSONResponse:
    """Geef canonieke codesets met labels voor API/UI-clients."""
    return JSONResponse({"codes": codes_en_labels()})


@app.get("/api/v1/referenties/input-hints")
def referenties_input_hints_endpoint() -> JSONResponse:
    """Geef required velden en defaults voor UI-form generatie."""
    return JSONResponse({"hints": input_hints()})


@app.post("/api/v1/import/mpo/pdf")
async def import_mpo_pdf_endpoint(bestand: UploadFile = File(...)) -> JSONResponse:
    """Parseer een MPO-PDF en geef herkenbare pensioenrecords terug voor UI-import."""
    naam = (bestand.filename or "").lower()
    if not naam.endswith(".pdf"):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_file_type",
                "message": "Alleen PDF-bestanden zijn toegestaan voor dit endpoint.",
            },
        )

    inhoud = await bestand.read()
    if not inhoud:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "empty_file",
                "message": "Het geuploade PDF-bestand is leeg.",
            },
        )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(inhoud)
        tmp_pad = Path(tmp.name)

    try:
        records = MPOParser.parse_pdf(tmp_pad)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "mpo_pdf_parse_error",
                "message": str(exc),
            },
        ) from exc
    finally:
        os.unlink(tmp_pad)

    return JSONResponse(
        {
            "records": naar_json_compatibel(records),
            "aantal_records": len(records),
        }
    )


@app.post("/api/v1/berekeningen")
def berekening_endpoint(request: BerekeningRequest) -> JSONResponse:
    """Bereken de huishoudcashflow voor één scenario."""
    if request.scenario.is_derived_scenario() and not request.scenario_lijst:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "derived_scenario_requires_list",
                "message": "Afgeleid scenario vereist scenario_lijst inclusief parent(s).",
            },
        )

    scenario_lijst = request.scenario_lijst or [request.scenario]
    _valideer_inheritance(scenario_lijst)

    try:
        cashflow = bereken_resultaten(
            scenario=request.scenario,
            persoon1=request.persoon1,
            persoon2=request.persoon2,
            records1=request.records1,
            records2=request.records2,
            jaar_van=request.jaar_van,
            jaar_tot=request.jaar_tot,
            scenario_lijst=scenario_lijst,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "berekening_input_error", "message": str(exc)},
        ) from exc

    return JSONResponse(
        {
            "cashflow": naar_json_compatibel(cashflow),
            "aannames": naar_json_compatibel(cashflow.aannames),
            "output_contract": OUTPUT_CONTRACT,
        }
    )


@app.post("/api/v1/vergelijkingen")
def vergelijking_endpoint(request: VergelijkingRequest) -> JSONResponse:
    """Vergelijk meerdere scenario's op dezelfde invoerset."""
    _valideer_inheritance(request.scenarios)

    vergelijking = vergelijk_scenarios(
        scenarios=request.scenarios,
        persoon1=request.persoon1,
        persoon2=request.persoon2,
        records1=request.records1,
        records2=request.records2,
        jaar_van=request.jaar_van,
        jaar_tot=request.jaar_tot,
    )

    payload = naar_json_compatibel(vergelijking)
    beste = vergelijking.beste_scenario_netto
    # Properties worden niet meegenomen door dataclass-serialisatie.
    # Geef de enginekeuze door zonder de volledige cashflow te dupliceren.
    payload["beste_scenario_netto"] = {"scenario_naam": beste.scenario_naam} if beste else None
    return JSONResponse({"vergelijking": payload})


@app.post("/api/v1/simulaties/actuarieel")
def actuariele_schatting_endpoint(request: ActuarieleSchattingRequest) -> JSONResponse:
    basis=request.berekening
    lijst=basis.scenario_lijst or [basis.scenario]
    _valideer_inheritance(lijst)
    persoon=basis.persoon1 if request.keuze.persoon=="P1" else basis.persoon2
    if persoon is None:
        raise HTTPException(status_code=422,detail="Voeg eerst de partner toe aan je scenario.")
    try:
        scenarios,raming=bouw_actuariele_scenarios(resolve_scenario(basis.scenario,lijst),persoon,
                                                 request.keuze,basis.jaar_van,basis.jaar_tot)
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc)) from exc
    if not raming["volledig"]:
        # Alleen losse pensioenramingen: geen volledige huishoudvergelijking
        # suggereren wanneer een pensioenpost niet kan worden aangepast.
        raming["totale_premie"]=None
        return JSONResponse(naar_json_compatibel({"raming":raming,"vergelijking":None}))
    vergelijking=vergelijk_scenarios(scenarios,basis.persoon1,basis.persoon2,basis.records1,basis.records2,
                                    basis.jaar_van,basis.jaar_tot)
    met=vergelijking.scenario_resultaten[2].cashflow
    zonder=vergelijking.scenario_resultaten[1].cashflow
    raming["totale_premie"]=sum((j.huishoudelijke_uitgaven for j in met.jaren),Decimal("0"))-sum((j.huishoudelijke_uitgaven for j in zonder.jaren),Decimal("0"))
    raming["aannames"]+=list(dict.fromkeys(a for item in vergelijking.scenario_resultaten for a in item.cashflow.aannames))
    return JSONResponse(naar_json_compatibel({"raming":raming,"vergelijking":vergelijking,"varianten":scenarios,
        "jaarvergelijking":bouw_actuariele_jaarvergelijking(vergelijking,persoon),
        "output_contract":OUTPUT_CONTRACT}))


@app.post("/api/v1/simulaties/pensioenopbouw")
def pensioenopbouw_endpoint(request: PensioenopbouwRequest) -> JSONResponse:
    basis = request.berekening
    lijst = basis.scenario_lijst or [basis.scenario]
    _valideer_inheritance(lijst)
    try:
        opgelost = resolve_scenario(basis.scenario, lijst)
        scenarios = bouw_opbouwscenarios(opgelost, request.keuze)
        persoon = opgelost.componenten[request.keuze.pensioen_index].persoon
        deelnemer = basis.persoon1 if persoon == "P1" else basis.persoon2
        if deelnemer is None:
            raise ValueError("Deze pensioenpost hoort bij een ontbrekende partner.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    vergelijking = vergelijk_scenarios(scenarios, basis.persoon1, basis.persoon2,
                                      basis.records1, basis.records2, basis.jaar_van, basis.jaar_tot)
    return JSONResponse(naar_json_compatibel({
        "vergelijking": vergelijking,
        "opbouw": bouw_opbouwuitkomst(vergelijking, request.keuze, deelnemer.geboortedatum),
        "keuze": request.keuze,
        "aannames": [
            "De ingevulde pensioenbedragen zijn aannames." if request.keuze.modus == "aannames" else "De uitvoerdersgegevens zijn door jou ingevuld; de app heeft ze niet bij de uitvoerder geverifieerd.",
            "De premie is een extra uitgave, inclusief het eventuele werkgeversdeel. Er is geen belastingaftrek voor de premie toegepast.",
            "Vrijwillige voortzetting en het opgegeven pensioen zijn niet gegarandeerd door deze simulatie; bevestig de mogelijkheden bij je uitvoerder.",
            "Alleen de gekozen pensioenpost en het werkinkomen van die persoon veranderen. Andere pensioenposten en de partner blijven ongewijzigd.",
            "De bestaande rendements- en indexatieaannames blijven gelden. De opgegeven pensioenbedragen gelden vanaf de gekozen pensioendatum.",
            "Het omslagpunt vergelijkt cumulatieve netto cashflow met en zonder doorbetalen, inclusief berekend rendement, tot het einde van de horizon; geen levenslange garantie.",
        ] + list(dict.fromkeys(aanname for item in vergelijking.scenario_resultaten for aanname in item.cashflow.aannames)),
    }))


@app.post("/api/v1/rapportages/excel")
def rapportage_excel_endpoint(request: RapportageRequest) -> Response:
    """Genereer een Excel-rapport op basis van de requestdata."""
    basis = request.berekening

    if basis.scenario.is_derived_scenario() and not basis.scenario_lijst:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "derived_scenario_requires_list",
                "message": "Afgeleid scenario vereist scenario_lijst inclusief parent(s).",
            },
        )

    scenario_lijst = basis.scenario_lijst or [basis.scenario]
    _valideer_inheritance(scenario_lijst)

    cashflow = bereken_resultaten(
        scenario=basis.scenario,
        persoon1=basis.persoon1,
        persoon2=basis.persoon2,
        records1=basis.records1,
        records2=basis.records2,
        jaar_van=basis.jaar_van,
        jaar_tot=basis.jaar_tot,
        scenario_lijst=scenario_lijst,
    )

    vergelijking = None
    if request.include_vergelijking:
        scenarios = request.scenarios_vergelijking or scenario_lijst
        _valideer_inheritance(scenarios)
        vergelijking = vergelijk_scenarios(
            scenarios=scenarios,
            persoon1=basis.persoon1,
            persoon2=basis.persoon2,
            records1=basis.records1,
            records2=basis.records2,
            jaar_van=basis.jaar_van,
            jaar_tot=basis.jaar_tot,
        )

    inhoud = genereer_rapport(cashflow=cashflow, vergelijking=vergelijking)
    return Response(
        content=inhoud,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=pensioen_rapport.xlsx",
        },
    )
