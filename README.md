# TaxTreat CZ legal ingestion package

This package builds a verifiable Czech-source document repository and SQLite registry for the WHT module.

## Included now
- Seed registry of 99 Czech income-tax treaty partners, based on the Czech Ministry of Finance overview stated as current at 4 February 2026.
- Crawler for the Ministry treaty overview and the Ministry guidance/notices overview.
- Discovery and download of linked treaties, protocols, MLI notices, Financial Bulletins, corrections and related official instruments.
- Direct ingestion targets for the OECD Czech MLI position and EUR-Lex Parent–Subsidiary Directive.
- SHA-256 checksum and immutable local file path for each downloaded document.
- JSON manifest and SQLite database builder.

## Run
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python run.py
```

Outputs:
- `data/raw/**` downloaded official documents
- `data/processed/document_manifest.json`
- `data/processed/taxtreat_cz.sqlite`

## Important boundary
This is the ingestion layer. It does not claim that treaty Articles 10, 11 and 12, protocols, MLI matching, domestic-law conditions or historical applicability have already been legally parsed and independently verified. Those require a separate parser and QA layer before production conclusions are issued.
