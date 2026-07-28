from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from taxtreat_cz.crawler import Crawler
from taxtreat_cz.build_db import build


if __name__ == "__main__":
    print("1/2 Spouštím stahování dokumentů...", flush=True)
    documents = Crawler(ROOT).run()

    downloaded = sum(doc.status == "downloaded" for doc in documents)
    if downloaded == 0:
        print("Nebyl stažen žádný dokument. Databáze se nebude přepisovat.", flush=True)
        raise SystemExit(1)

    print("2/2 Spouštím zpracování a sestavení databáze...", flush=True)
    build(ROOT)
    print("Hotovo.", flush=True)
