# Windows helpers

See `win-setup.bat`, `win-run-api.bat`, `win-run-web.bat`, `win-run-telegram.bat`.

Knowledge index (when present):
- `win-index-knowledge.bat` / `win-index-knowledge.ps1`
- Runbook: `docs/KNOWLEDGE_INDEX_RUNBOOK.md`
- Drive folder: `1Jx0cipUqQyGnJk4hFCURzWIg1Abo1Del`

```powershell
cd D:\AI\GitHub\mousavitax-platform
.\scripts\win-setup.bat
$env:EMBEDDING_PROVIDER="fallback"
$env:VECTOR_DB_PATH="$PWD\data\iran_tax_vectors.json"
python scripts\seed_knowledge.py
.\scripts\win-run-api.bat
```
