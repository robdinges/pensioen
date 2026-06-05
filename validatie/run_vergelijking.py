#!/usr/bin/env python3
"""CLI tool voor het uitvoeren van belastingvergelijkingen.

Gebruik:
    python validatie/run_vergelijking.py \\
        --input /pad/naar/dutch_tax/submissions/frits.json \\
        --jaar 2026 \\
        --geboortedatum-p1 1960-05-15 \\
        --output rapport.md

Optioneel:
    --geboortedatum-p2 1962-03-20  (indien fiscaal partner)
    --excel rapport.xlsx           (genereer ook Excel rapport)
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

from validatie.belasting_vergelijking.rapport_generator import (
    schrijf_excel_bestand,
    schrijf_markdown_bestand,
)
from validatie.belasting_vergelijking.vergelijker import vergelijk_berekeningen


def parse_datum(datum_str: str) -> date:
    """Parse datum string (YYYY-MM-DD) naar date object."""
    try:
        dt = datetime.strptime(datum_str, "%Y-%m-%d")
        return dt.date()
    except ValueError as e:
        raise ValueError(
            f"Ongeldige datum '{datum_str}'. Gebruik formaat YYYY-MM-DD (bijv. 1960-05-15)"
        ) from e


def main() -> int:
    """Main entry point voor CLI tool."""
    parser = argparse.ArgumentParser(
        description="Vergelijk dutch_tax submission met pensioen-app berekening",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Pad naar dutch_tax submission JSON bestand (bijv. frits.json)",
    )
    
    parser.add_argument(
        "--jaar",
        "-j",
        type=int,
        default=2026,
        help="Belastingjaar voor berekening (standaard: 2026)",
    )
    
    parser.add_argument(
        "--geboortedatum-p1",
        type=str,
        required=True,
        help="Geboortedatum persoon 1 (formaat: YYYY-MM-DD, bijv. 1960-05-15)",
    )
    
    parser.add_argument(
        "--geboortedatum-p2",
        type=str,
        help="Geboortedatum persoon 2 / fiscaal partner (formaat: YYYY-MM-DD)",
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("vergelijking_rapport.md"),
        help="Pad voor markdown output (standaard: vergelijking_rapport.md)",
    )
    
    parser.add_argument(
        "--excel",
        "-x",
        type=Path,
        help="Optioneel: genereer ook Excel rapport op dit pad",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Toon uitgebreide logging",
    )
    
    args = parser.parse_args()
    
    # Valideer input bestand
    if not args.input.exists():
        print(f"❌ FOUT: Input bestand niet gevonden: {args.input}", file=sys.stderr)
        return 1
    
    # Parse geboortedatums
    try:
        gb_p1 = parse_datum(args.geboortedatum_p1)
        gb_p2 = parse_datum(args.geboortedatum_p2) if args.geboortedatum_p2 else None
    except ValueError as e:
        print(f"❌ FOUT: {e}", file=sys.stderr)
        return 1
    
    if args.verbose:
        print(f"📂 Input: {args.input}")
        print(f"📅 Jaar: {args.jaar}")
        print(f"👤 Geboortedatum P1: {gb_p1}")
        if gb_p2:
            print(f"👥 Geboortedatum P2: {gb_p2}")
        print()
    
    # Voer vergelijking uit
    try:
        print(f"🔄 Vergelijking uitvoeren...")
        resultaat = vergelijk_berekeningen(
            json_pad=args.input,
            doel_jaar=args.jaar,
            geboortedatum_p1=gb_p1,
            geboortedatum_p2=gb_p2,
        )
        print(f"✅ Vergelijking voltooid")
        print()
        
        # Toon samenvatting
        print(f"📊 Samenvatting:")
        print(f"   Huishouden: {resultaat.huishouden_id}")
        print(f"   Verschillen: {len(resultaat.verschillen)}")
        print(
            f"   Kritiek: {resultaat.aantal_kritieke_verschillen}, "
            f"Significant: {resultaat.aantal_significante_verschillen}"
        )
        print()
        
        if resultaat.aanbevelingen:
            print(f"🎯 Top aanbevelingen:")
            for idx, aanbeveling in enumerate(resultaat.aanbevelingen[:3], 1):
                # Korte versie (eerste 80 chars)
                kort = aanbeveling[:80] + "..." if len(aanbeveling) > 80 else aanbeveling
                print(f"   {idx}. {kort}")
            print()
        
    except FileNotFoundError as e:
        print(f"❌ FOUT: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ FOUT tijdens vergelijking: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Schrijf markdown rapport
    try:
        print(f"📝 Markdown rapport schrijven naar: {args.output}")
        schrijf_markdown_bestand(resultaat, args.output)
        print(f"✅ Markdown rapport opgeslagen")
    except Exception as e:
        print(f"❌ FOUT bij schrijven markdown: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    # Schrijf Excel rapport (indien gevraagd)
    if args.excel:
        try:
            print(f"📊 Excel rapport schrijven naar: {args.excel}")
            schrijf_excel_bestand(resultaat, args.excel)
            print(f"✅ Excel rapport opgeslagen")
        except ImportError as e:
            print(
                f"⚠️  WAARSCHUWING: Excel export overgeslagen (openpyxl niet geïnstalleerd)",
                file=sys.stderr,
            )
            if args.verbose:
                print(f"   Details: {e}", file=sys.stderr)
        except Exception as e:
            print(f"❌ FOUT bij schrijven Excel: {e}", file=sys.stderr)
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    print()
    print(f"🎉 Klaar! Bekijk het rapport: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
