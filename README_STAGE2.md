# TaxTreat CZ – Stage 2

Tento balíček je **ověřený výstup z reálně stažených dat** z balíčku v1.
Neobsahuje znovu 342 MB souborů `data/raw`, aby šel snadno stáhnout.

## Co bylo skutečně provedeno

- vybráno 113 relevantních dokumentů (`treaty_or_statute`, `protocol`, `mli`, `eu_directive`),
- rozpoznán skutečný formát souborů podle jejich obsahu, nikoli podle přípony,
- text úspěšně extrahován z 99 dokumentů,
- 14 dokumentů zůstalo nezpracovaných (zejména naskenovaná PDF bez textové vrstvy a několik HTML shellů e-Sbírky),
- nalezeno 40 kandidátů pro článek 10, 41 pro článek 11 a 39 pro článek 12,
- výsledek uložen do SQLite databáze.

Kandidáty je nutné dále právně a technicky validovat. Nejde ještě o databázi ověřených sazeb.

## Co obsahuje

- `run_stage2.py` – opakovatelné zpracování nad původní složkou s `data/raw`,
- `data/processed/taxtreat_cz.sqlite` – databáze po Stage 2,
- `data/processed/stage2_extraction_report.json` – přesný report úspěchů a chyb,
- `data/processed/article_candidates_index.csv` – snadno otevřitelný index kandidátů článků,
- `requirements.txt` – závislosti včetně `pypdf`.

## Jak výsledek použít

Nejjednodušší je otevřít `article_candidates_index.csv` v Excelu. Pro detailní práci otevři `taxtreat_cz.sqlite` v DB Browser for SQLite.

Nové tabulky:

- `parsed_documents` – extrahovaný text a stav zpracování,
- `article_candidates` – kandidátní úseky článků 10–12.

Užitečný SQL dotaz:

```sql
SELECT d.title, d.kind, a.article_number, a.heading, a.excerpt, d.url
FROM article_candidates a
JOIN documents d ON d.id = a.document_id
ORDER BY d.title, a.article_number;
```

## Opakované spuštění na původní složce v1

Zkopíruj `run_stage2.py` do hlavní složky původního balíčku v1 a spusť:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -u run_stage2.py
```

Původní `data/raw` musí zůstat na místě.
