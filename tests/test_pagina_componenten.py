"""Regression tests for the financial components page."""

from pensioen.ui.pagina_componenten import _aantal_tegelkolommen, _laad_aow_bedragen


def test_huidige_belastingconfig_bevat_aow_bedragen() -> None:
    """The UI must unpack the loader result before reading AOW amounts."""
    gehuwd, alleenstaand = _laad_aow_bedragen(2026)

    assert gehuwd is not None and gehuwd > 0
    assert alleenstaand is not None and alleenstaand > 0


def test_compacte_layout_toont_meer_tegelkolommen() -> None:
    assert _aantal_tegelkolommen("kleur") == 3
    assert _aantal_tegelkolommen("compact") == 4
    assert _aantal_tegelkolommen("werkblad") == 3
