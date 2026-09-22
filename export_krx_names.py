"""stock-pipeline 의 history.db corp_master 에서 현재 상장사 목록을 뽑아 data/krx_names.csv 로 저장한다.

    .venv\\Scripts\\python.exe export_krx_names.py

루틴이 "주목할 만한 것"에 회사명을 적기 전에 상장 여부를 확인하는 근거 파일이다. 월 1회쯤 갱신하면 된다
(신규 상장·상폐 반영). history.db 는 옮길 수 없으므로 노트북에서만 돌아간다.
"""
import csv
import sqlite3
from pathlib import Path

DB = Path(r"C:\claude\stock-pipeline\db\history.db")
OUT = Path(__file__).resolve().parent / "data" / "krx_names.csv"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
rows = con.execute("SELECT ticker, corp_name, market FROM corp_master WHERE is_delisted=0 ORDER BY ticker").fetchall()
OUT.parent.mkdir(exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ticker", "name", "market"])
    w.writerows(rows)
print(f"{len(rows)} rows -> {OUT}")
