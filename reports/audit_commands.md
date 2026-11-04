# Reproducer auditforberedelsen

Fra `/workspace/EM-solver`:

```sh
pdftotext -layout data/sources/exams.pdf data/exams_extracted.txt
pdftotext -layout data/sources/answers.pdf data/answers_extracted.txt
/workspace/em1-venv/bin/python tools/build_audit.py
/workspace/em1-venv/bin/python -m pytest -q
/workspace/em1-venv/bin/python tools/build_coverage.py
```

Alle disse trin bruger lokale filer. Appen startes med:

```sh
/workspace/em1-venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```
Python-miljøet ligger i `/workspace/em1-venv`, og dets fastlåste versioner i
`requirements-lock.txt` i repoet. Afhængigheder er installeret under udviklingen;
ingen internetadgang er nødvendig til at genopbygge auditrapporten eller køre integritetstestene.
