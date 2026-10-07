Set-Location (Join-Path $PSScriptRoot '..')
.\.venv\Scripts\python -m src.seeds.seed_courses
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
.\.venv\Scripts\python -m src.seeds.seed_students
exit $LASTEXITCODE
