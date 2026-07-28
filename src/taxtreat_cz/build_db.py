from __future__ import annotations
import csv, json, sqlite3
from pathlib import Path

def build(root: Path):
    db=root/'data'/'processed'/'taxtreat_cz.sqlite'
    if db.exists(): db.unlink()
    con=sqlite3.connect(db)
    con.executescript('''
    CREATE TABLE treaty_registry(
      id INTEGER PRIMARY KEY,
      country_cs TEXT NOT NULL UNIQUE,
      effective_from TEXT NOT NULL,
      source_status_date TEXT NOT NULL
    );
    CREATE TABLE documents(
      id INTEGER PRIMARY KEY,
      url TEXT NOT NULL UNIQUE,
      source_page TEXT,
      title TEXT,
      kind TEXT,
      mime_type TEXT,
      sha256 TEXT,
      local_path TEXT,
      downloaded_at TEXT,
      status TEXT,
      error TEXT
    );
    CREATE INDEX idx_documents_kind ON documents(kind);
    CREATE INDEX idx_documents_status ON documents(status);
    ''')
    with (root/'data'/'processed'/'cz_treaty_registry_seed.csv').open(encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    con.executemany('INSERT INTO treaty_registry(country_cs,effective_from,source_status_date) VALUES(:country_cs,:effective_from,:source_status_date)',rows)
    manifest=root/'data'/'processed'/'document_manifest.json'
    if manifest.exists():
        docs=json.loads(manifest.read_text(encoding='utf-8'))
        con.executemany('''INSERT INTO documents(url,source_page,title,kind,mime_type,sha256,local_path,downloaded_at,status,error)
                           VALUES(:url,:source_page,:title,:kind,:mime_type,:sha256,:local_path,:downloaded_at,:status,:error)''',docs)
    con.commit(); con.close()
    print(db)

if __name__=='__main__': build(Path(__file__).resolve().parents[2])
