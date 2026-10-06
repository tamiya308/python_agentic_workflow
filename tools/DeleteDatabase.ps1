# Deletes data/students.db (all students and courses). It is recreated empty on the next
# server start or seed. Asks for confirmation unless -Force is passed.
param([switch]$Force)

Set-Location (Join-Path $PSScriptRoot '..')
$db = 'data\students.db'

if (-not (Test-Path $db)) {
    Write-Host "$db does not exist; nothing to delete."
    exit 0
}

if (-not $Force) {
    $answer = Read-Host "Delete $db and every record in it? Type 'yes' to confirm"
    if ($answer -ne 'yes') {
        Write-Host 'Cancelled.'
        exit 1
    }
}

try {
    # SQLite may leave journal files next to the database; remove them too.
    foreach ($file in @($db, "$db-journal", "$db-wal", "$db-shm")) {
        if (Test-Path $file) { Remove-Item $file -ErrorAction Stop }
    }
}
catch {
    Write-Error "Could not delete ${db}: $($_.Exception.Message) Stop the server first; it keeps the file open."
    exit 1
}

Write-Host "Deleted $db."
exit 0
