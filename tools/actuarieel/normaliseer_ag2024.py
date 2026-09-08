"""Normaliseer het openbare AG2024-Excelbestand naar de offline rekenbron.

Gebruik: python3 tools/actuarieel/normaliseer_ag2024.py /pad/AG2024.xlsx
Download: https://www.actuarieelgenootschap.nl/download/parameters-en-best-estimate-sterftekansen-van-prognosetafel-ag2024-excel
"""
from pathlib import Path
import hashlib
import json
import sys
from openpyxl import load_workbook


def main() -> None:
    path=Path(sys.argv[1]); workbook=load_workbook(path,read_only=True,data_only=True)
    data={'versie':'AG2024','bron':'https://www.actuarieelgenootschap.nl/kennisbank/prognosetafel-ag2024-2',
          'sha256_xlsx':hashlib.sha256(path.read_bytes()).hexdigest(),
          'jaar_van':2025,'jaar_tot':2200,'leeftijd_tot':120,'qx':{}}
    for sex,sheet in [('man','qx mannen 2024'),('vrouw','qx vrouwen 2024')]:
        rows=list(workbook[sheet].values)
        cols=[i for i,y in enumerate(rows[0]) if isinstance(y,int) and 2025<=y<=2200]
        assert len(cols)==176
        data['qx'][sex]=[[str(row[i]) for i in cols] for row in rows[1:] if isinstance(row[0],int)]
        assert len(data['qx'][sex])==121
    Path('config/actuarieel_ag2024.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')


if __name__=='__main__':
    main()
