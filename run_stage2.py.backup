from pathlib import Path
import json
import re
import sqlite3
import hashlib
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'data' / 'processed' / 'taxtreat_cz.sqlite'
REPORT_PATH = ROOT / 'data' / 'processed' / 'stage2_extraction_report.json'
RELEVANT_KINDS = ('treaty_or_statute', 'protocol', 'mli', 'eu_directive')

ARTICLE_PATTERNS = {
    10: [
        r'(?im)^\s*(?:ČLÁNEK|Článek|ARTICLE|Article|ARTIKEL|Artikel)\s*(?:10|X)\b[^\n]*',
        r'(?im)^\s*10[\s\.\-]+(?:DIVIDENDY|DIVIDENDS|DIVIDENDEN)\b[^\n]*',
    ],
    11: [
        r'(?im)^\s*(?:ČLÁNEK|Článek|ARTICLE|Article|ARTIKEL|Artikel)\s*(?:11|XI)\b[^\n]*',
        r'(?im)^\s*11[\s\.\-]+(?:ÚROKY|UROKY|INTEREST|ZINSEN)\b[^\n]*',
    ],
    12: [
        r'(?im)^\s*(?:ČLÁNEK|Článek|ARTICLE|Article|ARTIKEL|Artikel)\s*(?:12|XII)\b[^\n]*',
        r'(?im)^\s*12[\s\.\-]+(?:LICENČNÍ POPLATKY|LICENCNI POPLATKY|ROYALTIES|LIZENZGEBÜHREN|LIZENZGEBUHREN)\b[^\n]*',
    ],
}
NEXT_ARTICLE_RE = re.compile(
    r'(?im)^\s*(?:ČLÁNEK|Článek|ARTICLE|Article|ARTIKEL|Artikel)\s*(?:\d{1,2}|[IVX]{1,5})\b[^\n]*'
)


def normalize_path(value: str) -> Path:
    return ROOT / Path(value.replace('\\', '/'))


def detect_format(path: Path) -> str:
    head = path.read_bytes()[:16]
    if head.startswith(b'%PDF-'):
        return 'pdf'
    if head.startswith(b'PK\x03\x04'):
        return 'zip'
    low = head.lower().lstrip()
    if low.startswith((b'<!doctype', b'<html', b'<?xml', b'<')):
        return 'html'
    return 'binary'


def extract_pdf(path: Path) -> tuple[str, int]:
    reader = PdfReader(str(path), strict=False)
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or '')
        except Exception:
            pages.append('')
    return '\n\n'.join(pages), len(reader.pages)


def extract_html(path: Path) -> tuple[str, int]:
    raw = path.read_bytes()
    for enc in ('utf-8', 'windows-1250', 'iso-8859-2', 'latin-1'):
        try:
            html = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        html = raw.decode('utf-8', errors='replace')
    soup = BeautifulSoup(html, 'lxml')
    for tag in soup(['script', 'style', 'noscript', 'svg']):
        tag.decompose()
    return soup.get_text('\n', strip=True), 1


def clean_text(text: str) -> str:
    text = text.replace('\x00', '').replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n[ \t]+', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def find_article(text: str, article_no: int) -> tuple[int, int, str, str] | None:
    # Primary: explicit article heading. The loose Czech pattern also handles
    # damaged text extracted from older Sbírka PDFs (e.g. "CÏ laÂ nek 10").
    loose_heading = {
        10: r'(?im)^\s*(?:ČLÁNEK|Článek|C.{0,4}la.{0,4}nek|ARTICLE|Article|ARTIKEL|Artikel)\s*(?:10|X)\b[^\n]*',
        11: r'(?im)^\s*(?:ČLÁNEK|Článek|C.{0,4}la.{0,4}nek|ARTICLE|Article|ARTIKEL|Artikel)\s*(?:11|XI)\b[^\n]*',
        12: r'(?im)^\s*(?:ČLÁNEK|Článek|C.{0,4}la.{0,4}nek|ARTICLE|Article|ARTIKEL|Artikel)\s*(?:12|XII)\b[^\n]*',
    }[article_no]
    hits = list(re.finditer(loose_heading, text))

    # Secondary: topic heading. This is more reliable for protocols, where
    # the protocol's own Article X does not necessarily mean DTT Article 10.
    topic = {
        10: r'(?im)^\s*(?:DIVIDENDY|DIVIDENDS|DIVIDENDEN)\s*$',
        11: r'(?im)^\s*(?:ÚROKY|U.{0,3}ROKY|INTEREST|ZINSEN)\s*$',
        12: r'(?im)^\s*(?:LICENČNÍ\s+POPLATKY|LICENCNI\s+POPLATKY|LICEN.{0,5}POPLATKY|ROYALTIES|LIZENZGEB.{0,5}HREN)\s*$',
    }[article_no]
    topic_hits = list(re.finditer(topic, text))

    if hits:
        hit = min(hits, key=lambda m: m.start())
        start = hit.start()
        heading = hit.group(0).strip()
    elif topic_hits:
        hit = min(topic_hits, key=lambda m: m.start())
        start = max(0, hit.start() - 250)
        heading = hit.group(0).strip()
    else:
        return None

    end = min(len(text), hit.end() + 16000)
    # End at the next recognisable article heading.
    for nxt in NEXT_ARTICLE_RE.finditer(text, hit.end()):
        if nxt.start() - start < 150:
            continue
        end = nxt.start()
        break
    # If damaged encoding prevents next-heading recognition, cap the excerpt.
    if end - start > 16000:
        end = start + 16000
    excerpt = text[start:end].strip()
    return start, end, heading, excerpt


def ensure_schema(db: sqlite3.Connection) -> None:
    db.executescript('''
    CREATE TABLE IF NOT EXISTS parsed_documents (
      document_id INTEGER PRIMARY KEY,
      detected_format TEXT NOT NULL,
      page_count INTEGER,
      char_count INTEGER NOT NULL,
      text_sha256 TEXT,
      extracted_text TEXT,
      extraction_status TEXT NOT NULL,
      extraction_error TEXT,
      extracted_at TEXT NOT NULL,
      FOREIGN KEY(document_id) REFERENCES documents(id)
    );
    CREATE TABLE IF NOT EXISTS article_candidates (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      document_id INTEGER NOT NULL,
      article_number INTEGER NOT NULL,
      heading TEXT,
      start_char INTEGER,
      end_char INTEGER,
      excerpt TEXT NOT NULL,
      extraction_method TEXT NOT NULL,
      UNIQUE(document_id, article_number),
      FOREIGN KEY(document_id) REFERENCES documents(id)
    );
    CREATE INDEX IF NOT EXISTS idx_article_candidates_doc ON article_candidates(document_id);
    CREATE INDEX IF NOT EXISTS idx_article_candidates_no ON article_candidates(article_number);
    ''')


def main() -> None:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    ensure_schema(db)
    docs = db.execute(
        f"SELECT id,title,kind,url,local_path,status FROM documents WHERE kind IN ({','.join('?'*len(RELEVANT_KINDS))}) ORDER BY id",
        RELEVANT_KINDS,
    ).fetchall()

    stats = {
        'started_at': datetime.now(timezone.utc).isoformat(),
        'documents_selected': len(docs),
        'parsed': 0,
        'failed': 0,
        'missing_files': 0,
        'formats': {},
        'article_candidates': {'10': 0, '11': 0, '12': 0},
        'failures': [],
    }
    now = datetime.now(timezone.utc).isoformat()
    db.execute('DELETE FROM article_candidates')

    for i, doc in enumerate(docs, 1):
        path = normalize_path(doc['local_path'])
        print(f"[{i}/{len(docs)}] {doc['kind']}: {doc['title']}", flush=True)
        if not path.exists():
            stats['failed'] += 1
            stats['missing_files'] += 1
            err = f'Missing file: {path}'
            stats['failures'].append({'document_id': doc['id'], 'title': doc['title'], 'error': err})
            db.execute('''INSERT OR REPLACE INTO parsed_documents
                (document_id,detected_format,page_count,char_count,text_sha256,extracted_text,extraction_status,extraction_error,extracted_at)
                VALUES (?,?,?,?,?,?,?,?,?)''', (doc['id'],'missing',None,0,None,None,'failed',err,now))
            continue
        fmt = detect_format(path)
        stats['formats'][fmt] = stats['formats'].get(fmt, 0) + 1
        try:
            if fmt == 'pdf':
                text, pages = extract_pdf(path)
            elif fmt == 'html':
                text, pages = extract_html(path)
            else:
                raise ValueError(f'Unsupported detected format: {fmt}')
            text = clean_text(text)
            if len(text) < 40:
                raise ValueError(f'Extracted text too short ({len(text)} chars)')
            sha = hashlib.sha256(text.encode('utf-8')).hexdigest()
            db.execute('''INSERT OR REPLACE INTO parsed_documents
                (document_id,detected_format,page_count,char_count,text_sha256,extracted_text,extraction_status,extraction_error,extracted_at)
                VALUES (?,?,?,?,?,?,?,?,?)''', (doc['id'],fmt,pages,len(text),sha,text,'parsed',None,now))
            for no in (10,11,12):
                found = find_article(text, no)
                if found:
                    start,end,heading,excerpt = found
                    db.execute('''INSERT OR REPLACE INTO article_candidates
                      (document_id,article_number,heading,start_char,end_char,excerpt,extraction_method)
                      VALUES (?,?,?,?,?,?,?)''', (doc['id'],no,heading,start,end,excerpt,'heading_regex_v1'))
                    stats['article_candidates'][str(no)] += 1
            stats['parsed'] += 1
        except Exception as exc:
            stats['failed'] += 1
            err = f'{type(exc).__name__}: {exc}'
            stats['failures'].append({'document_id': doc['id'], 'title': doc['title'], 'format': fmt, 'error': err})
            db.execute('''INSERT OR REPLACE INTO parsed_documents
                (document_id,detected_format,page_count,char_count,text_sha256,extracted_text,extraction_status,extraction_error,extracted_at)
                VALUES (?,?,?,?,?,?,?,?,?)''', (doc['id'],fmt,None,0,None,None,'failed',err,now))
        if i % 10 == 0:
            db.commit()
    db.commit()
    stats['completed_at'] = datetime.now(timezone.utc).isoformat()
    REPORT_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\nStage 2 completed')
    print(f"Parsed: {stats['parsed']}/{stats['documents_selected']}")
    print(f"Failed: {stats['failed']}")
    for no in ('10','11','12'):
        print(f"Article {no} candidates: {stats['article_candidates'][no]}")
    print(DB_PATH)

if __name__ == '__main__':
    main()
