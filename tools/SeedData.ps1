Set-Location (Join-Path $PSScriptRoot '..')
.\.venv\Scripts\python -m src.seeds.seed_students
exit $LASTEXITCODE
