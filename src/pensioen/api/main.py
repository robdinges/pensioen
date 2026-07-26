"""FastAPI entrypoint voor de pensioenrekenengine."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse, Response

from pensioen.api.referentietabellen import codes_en_labels, input_hints
from pensioen.api.schemas import BerekeningRequest, RapportageRequest, VergelijkingRequest
from pensioen.api.serialisatie import naar_json_compatibel
from pensioen.calculations.resultaat_service import bereken_resultaten
from pensioen.calculations.inheritance_engine import validate_inheritance_tree
from pensioen.parsers.parser_mpo import MPOParser
from pensioen.calculations.scenario_engine import vergelijk_scenarios
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


OUTPUT_CONTRACT = {
    "versie": "1.0",
    "jaarresultaten": "cashflow.jaren[].jaar_samenvatting",
    "accountant": "cashflow.jaren[].accountant_detail",
    "maandresultaten": "cashflow.jaren[].maanden[]",
}


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

    return JSONResponse({"vergelijking": naar_json_compatibel(vergelijking)})


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
