import sqlite3
from pathlib import Path

conn = sqlite3.connect(r"data\processed\taxtreat_cz.sqlite")
cur = conn.cursor()

cur.execute("""
SELECT
    d.id,
    d.title,
    d.local_path
FROM parsed_documents p
JOIN documents d
    ON d.id = p.document_id
WHERE p.extraction_status = 'failed'
ORDER BY d.id
""")

for document_id, title, local_path in cur.fetchall():
    path = Path(local_path)

    print()
    print("ID:", document_id)
    print("Název:", title)
    print("Soubor:", local_path)

    if not path.exists():
        print("CHYBA: Soubor neexistuje")
        continue

    print("Velikost:", path.stat().st_size, "bytes")

    with path.open("rb") as file:
        first_bytes = file.read(40)

    print("Prvních 40 bytů:", first_bytes)

conn.close()