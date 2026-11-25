param(
    [string]$PythonExe = '',
    [int]$Port = 8088,
    [string]$DeployDir = 'C:\ProgramData\Jenkins\astrobot-live'
)

$ErrorActionPreference = 'Stop'

if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) {
        $PythonExe = $cmd.Source
    } elseif (Test-Path 'C:\Users\PMLS\AppData\Local\Programs\Python\Python312\python.exe') {
        $PythonExe = 'C:\Users\PMLS\AppData\Local\Programs\Python\Python312\python.exe'
    } else {
        throw 'Python executable not found.'
    }
}

Write-Output "Using Python: $PythonExe"
Write-Output "Deploy directory: $DeployDir"
Write-Output "Target port: $Port"

# Stop previously deployed instance if running (PID file + port listener check)
$pidFile = Join-Path $DeployDir 'astrobot.pid'
if (Test-Path $pidFile) {
    $oldPidText = (Get-Content -Path $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($oldPidText -match '^\d+$') {
        $oldPid = [int]$oldPidText
        $oldProc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
        if ($oldProc) {
            Write-Output "Stopping previous AstroBot PID $oldPid..."
            Stop-Process -Id $oldPid -Force -ErrorAction SilentlyContinue
            Wait-Process -Id $oldPid -Timeout 10 -ErrorAction SilentlyContinue
        }
    }
}

$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
foreach ($conn in $listeners) {
    if ($conn.OwningProcess -and $conn.OwningProcess -ne 0) {
        Write-Output "Stopping process $($conn.OwningProcess) listening on port $Port..."
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $conn.OwningProcess -Timeout 10 -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 1

New-Item -ItemType Directory -Path $DeployDir -Force | Out-Null
$targetAppDir = Join-Path $DeployDir 'astrobot'
if (Test-Path $targetAppDir) {
    Remove-Item -Path $targetAppDir -Recurse -Force
}

$sourceAppDir = Join-Path $PSScriptRoot 'astrobot'
if (-not (Test-Path $sourceAppDir)) {
    throw "Source directory not found: $sourceAppDir"
}
Copy-Item -Path $sourceAppDir -Destination $targetAppDir -Recurse -Force

# Clear Jenkins process-tree cookies so the live server survives after the build finishes
$env:JENKINS_NODE_COOKIE = 'dontKillMe'
$env:BUILD_ID = 'dontKillMe'
$env:HUDSON_COOKIE = 'dontKillMe'
$env:JENKINS_SERVER_COOKIE = 'dontKillMe'
$env:HUDSON_SERVER_COOKIE = 'dontKillMe'
$env:PORT = "$Port"
$env:PYTHONUTF8 = '1'
$env:PYTHONUNBUFFERED = '1'

$outLog = Join-Path $DeployDir 'astrobot.out.log'
$errLog = Join-Path $DeployDir 'astrobot.err.log'
$appPy = Join-Path $targetAppDir 'app.py'

$proc = Start-Process -FilePath $PythonExe `
    -ArgumentList @('-u', $appPy, '--port', "$Port") `
    -WorkingDirectory $targetAppDir `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

Set-Content -Path $pidFile -Value $proc.Id -Encoding ASCII
Write-Output "Started AstroBot live server (PID: $($proc.Id))"

# Health check
$healthy = $false
for ($i = 0; $i -lt 15; $i++) {
    try {
        $res = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 3
        if ($res.StatusCode -eq 200 -and $res.Content -match '"status"\s*:\s*"ok"') {
            $healthy = $true
            Write-Output "Health check passed: $($res.Content)"
            break
        }
    } catch {}
    Start-Sleep -Seconds 1
}

if (-not $healthy) {
    if (Test-Path $errLog) {
        Write-Output '--- astrobot.err.log ---'
        Get-Content $errLog
    }
    throw "AstroBot failed to become healthy on http://localhost:$Port"
}

$chatBody = '{"message":"Why is Mars red?"}'
$chatRes = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/chat" -Method Post -ContentType 'application/json' -Body $chatBody -UseBasicParsing -TimeoutSec 5
if ($chatRes.StatusCode -ne 200 -or $chatRes.Content -notmatch 'iron oxide') {
    throw "Chat API verification failed: $($chatRes.Content)"
}
Write-Output "Chat API check passed: $($chatRes.Content)"
Write-Output "LIVE URL: http://localhost:$Port"
