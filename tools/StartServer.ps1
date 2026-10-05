Set-Location (Join-Path $PSScriptRoot '..')
.\.venv\Scripts\python -m uvicorn src.main:app --reload
exit $LASTEXITCODE
