$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Path $PSScriptRoot -Parent
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$pidFile = Join-Path $projectRoot "quickshot.pid"

if (!(Test-Path $venvPython)) {
    Write-Host "Virtual environment not found. Creating .venv..."
    Push-Location $projectRoot
    try {
        py -m venv .venv
    }
    finally {
        Pop-Location
    }
}

Push-Location $projectRoot
try {
    if (Test-Path $pidFile) {
        $existingPid = (Get-Content $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
        if ($existingPid -match '^\d+$') {
            $existingProcess = Get-Process -Id ([int]$existingPid) -ErrorAction SilentlyContinue
            if ($null -ne $existingProcess) {
                Write-Host "Stopping previous QuickShot instance (PID $existingPid)..."
                Stop-Process -Id ([int]$existingPid) -Force
                Start-Sleep -Milliseconds 500
            }
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }

    & $venvPython -m pip --isolated install -e .
    & $venvPython -m quickshot.api.cli
}
finally {
    Pop-Location
}
