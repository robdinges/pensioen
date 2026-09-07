"""Tests voor audit trail models."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pensioen.models.audit import AuditEntry, MutationLog


def test_audit_entry_creation() -> None:
    """Test aanmaken van AuditEntry."""
    entry = AuditEntry(
        timestamp=datetime.now(),
        scenario_naam="Test Scenario",
        field_path="rendement_pct",
        old_value=Decimal("3"),
        new_value=Decimal("5"),
        is_override=True,
        user_process="react",
    )

    assert entry.scenario_naam == "Test Scenario"
    assert entry.field_path == "rendement_pct"
    assert entry.old_value == Decimal("3")
    assert entry.new_value == Decimal("5")
    assert entry.is_override is True


def test_audit_entry_repr() -> None:
    """Test string representatie van AuditEntry."""
    entry = AuditEntry(
        timestamp=datetime(2026, 5, 29, 10, 30, 0),
        scenario_naam="Test",
        field_path="rendement_pct",
        old_value=Decimal("3"),
        new_value=Decimal("5"),
        is_override=True,
    )

    repr_str = repr(entry)
    assert "2026-05-29 10:30:00" in repr_str
    assert "Test" in repr_str
    assert "rendement_pct" in repr_str
    assert "[OVERRIDE]" in repr_str


def test_audit_entry_format_value() -> None:
    """Test value formatting in audit entries."""
    entry = AuditEntry(
        timestamp=datetime.now(),
        scenario_naam="Test",
        field_path="test",
        old_value=None,
        new_value=Decimal("1000"),
        is_override=False,
    )

    assert entry._format_value(None) == "None"
    assert entry._format_value(Decimal("1000")) == "€1,000.00"
    assert entry._format_value(Decimal("0")) == "€0.00"
    assert entry._format_value([1, 2, 3]) == "[3 items]"
    assert entry._format_value({"a": 1, "b": 2}) == "{2 keys}"


def test_mutation_log_creation() -> None:
    """Test aanmaken van MutationLog."""
    log = MutationLog()
    assert len(log.entries) == 0
    assert isinstance(log.created_at, datetime)


def test_mutation_log_add_entry() -> None:
    """Test toevoegen van entries aan log."""
    log = MutationLog()
    
    entry1 = AuditEntry(
        timestamp=datetime.now(),
        scenario_naam="Scenario A",
        field_path="rendement_pct",
        old_value=Decimal("3"),
        new_value=Decimal("5"),
        is_override=False,
    )
    entry2 = AuditEntry(
        timestamp=datetime.now(),
        scenario_naam="Scenario B",
        field_path="inflatie_pct",
        old_value=Decimal("2"),
        new_value=Decimal("3"),
        is_override=True,
    )

    log.add_entry(entry1)
    log.add_entry(entry2)

    assert len(log.entries) == 2
    assert log.entries[0] == entry1
    assert log.entries[1] == entry2


def test_mutation_log_get_entries_for_scenario() -> None:
    """Test filteren van entries per scenario."""
    log = MutationLog()
    
    now = datetime.now()
    entry1 = AuditEntry(
        timestamp=now,
        scenario_naam="Scenario A",
        field_path="field1",
        old_value="old",
        new_value="new",
        is_override=False,
    )
    entry2 = AuditEntry(
        timestamp=now,
        scenario_naam="Scenario B",
        field_path="field2",
        old_value="old",
        new_value="new",
        is_override=False,
    )
    entry3 = AuditEntry(
        timestamp=now,
        scenario_naam="Scenario A",
        field_path="field3",
        old_value="old",
        new_value="new",
        is_override=True,
    )

    log.add_entry(entry1)
    log.add_entry(entry2)
    log.add_entry(entry3)

    entries_a = log.get_entries_for_scenario("Scenario A")
    assert len(entries_a) == 2
    assert all(e.scenario_naam == "Scenario A" for e in entries_a)

    entries_b = log.get_entries_for_scenario("Scenario B")
    assert len(entries_b) == 1
    assert entries_b[0].scenario_naam == "Scenario B"


def test_mutation_log_get_entries_for_field() -> None:
    """Test filteren van entries per veld."""
    log = MutationLog()
    
    entry1 = AuditEntry(
        timestamp=datetime.now(),
        scenario_naam="Test",
        field_path="rendement_pct",
        old_value=Decimal("3"),
        new_value=Decimal("4"),
        is_override=False,
    )
    entry2 = AuditEntry(
        timestamp=datetime.now(),
        scenario_naam="Test",
        field_path="rendement_pct",
        old_value=Decimal("4"),
        new_value=Decimal("5"),
        is_override=False,
    )
    entry3 = AuditEntry(
        timestamp=datetime.now(),
        scenario_naam="Test",
        field_path="inflatie_pct",
        old_value=Decimal("2"),
        new_value=Decimal("3"),
        is_override=False,
    )

    log.add_entry(entry1)
    log.add_entry(entry2)
    log.add_entry(entry3)

    entries_rendement = log.get_entries_for_field("Test", "rendement_pct")
    assert len(entries_rendement) == 2
    assert all(e.field_path == "rendement_pct" for e in entries_rendement)

    entries_inflatie = log.get_entries_for_field("Test", "inflatie_pct")
    assert len(entries_inflatie) == 1


def test_mutation_log_get_recent_entries() -> None:
    """Test ophalen van recente entries (reverse chronologisch)."""
    log = MutationLog()
    
    # Voeg entries toe met oplopende timestamps
    from datetime import timedelta
    base_time = datetime(2026, 5, 29, 10, 0, 0)
    
    for i in range(10):
        entry = AuditEntry(
            timestamp=base_time + timedelta(minutes=i),
            scenario_naam=f"Scenario {i}",
            field_path="field",
            old_value=i,
            new_value=i + 1,
            is_override=False,
        )
        log.add_entry(entry)

    # Haal 5 meest recente op
    recent = log.get_recent_entries(limit=5)
    assert len(recent) == 5
    # Eerste entry moet de nieuwste zijn (index 9)
    assert recent[0].scenario_naam == "Scenario 9"
    assert recent[4].scenario_naam == "Scenario 5"


def test_mutation_log_serialization() -> None:
    """Test serialisatie naar en van dict."""
    log = MutationLog()
    
    entry = AuditEntry(
        timestamp=datetime(2026, 5, 29, 10, 30, 0),
        scenario_naam="Test",
        field_path="rendement_pct",
        old_value=Decimal("3"),
        new_value=Decimal("5"),
        is_override=True,
        user_process="streamlit",
    )
    log.add_entry(entry)

    # Serialize
    data = log.to_dict()
    assert "created_at" in data
    assert "entries" in data
    assert len(data["entries"]) == 1
    assert data["entries"][0]["scenario_naam"] == "Test"
    assert data["entries"][0]["field_path"] == "rendement_pct"
    assert data["entries"][0]["old_value"] == "3"  # Decimal serialized als string
    assert data["entries"][0]["new_value"] == "5"
    assert data["entries"][0]["is_override"] is True

    # Deserialize
    log2 = MutationLog.from_dict(data)
    assert len(log2.entries) == 1
    assert log2.entries[0].scenario_naam == "Test"
    assert log2.entries[0].field_path == "rendement_pct"
    assert log2.entries[0].is_override is True


def test_mutation_log_empty_serialization() -> None:
    """Test serialisatie van lege log."""
    log = MutationLog()
    data = log.to_dict()
    
    assert "created_at" in data
    assert "entries" in data
    assert len(data["entries"]) == 0

    # Deserialize empty log
    log2 = MutationLog.from_dict(data)
    assert len(log2.entries) == 0


def test_mutation_log_limit_parameter() -> None:
    """Test limit parameter in get methods."""
    log = MutationLog()
    
    for i in range(20):
        entry = AuditEntry(
            timestamp=datetime.now(),
            scenario_naam="Test",
            field_path=f"field{i}",
            old_value=i,
            new_value=i + 1,
            is_override=False,
        )
        log.add_entry(entry)

    # Test limit in get_entries_for_scenario
    entries = log.get_entries_for_scenario("Test", limit=5)
    assert len(entries) == 5

    # Test limit in get_recent_entries
    recent = log.get_recent_entries(limit=10)
    assert len(recent) == 10
