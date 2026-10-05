Set-Location (Join-Path $PSScriptRoot '..')
.\.venv\Scripts\ruff format src tests
if ($LASTEXITCODE) { exit $LASTEXITCODE }
.\.venv\Scripts\python -m pytest
exit $LASTEXITCODE
