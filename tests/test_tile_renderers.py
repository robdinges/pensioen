"""Tests for financial tile icon selection."""

from pathlib import Path

import pytest

from pensioen.ui.tile_renderers import tegelicoon_pad


@pytest.mark.parametrize(
    ("sleutel", "bestandsnaam"),
    [
        ("arbeidsinkomen", "arbeidsinkomen.svg"),
        ("pensioen_inkomen", "pensioeninkomen.svg"),
        ("spaargeld", "sparen.svg"),
        ("beleggingen", "beleggen.svg"),
        ("eigen_woning", "eigen_woning.svg"),
    ],
)
def test_tegelicoon_pad_koppelt_domeintype_aan_bestaand_icoon(
    sleutel: str,
    bestandsnaam: str,
) -> None:
    pad = tegelicoon_pad(sleutel)

    assert pad.name == bestandsnaam
    assert pad.is_file()


def test_tegelicoon_pad_gebruikt_overig_als_fallback() -> None:
    pad = tegelicoon_pad("onbekend_type")

    assert pad == Path(pad.parent, "overig.svg")
    assert pad.is_file()
