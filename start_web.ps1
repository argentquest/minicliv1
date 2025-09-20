param(
    [string]$PythonPath = (Join-Path $PSScriptRoot 'venv' 'Scripts' 'python.exe'),
    [string]$BackendHost = 'http://localhost:8000',
    [string]$FrontendUrl = 'http://localhost:5173',
    [switch]$StartFrontend
)

function Normalize-Url {
    param(
        [string]$Url,
        [string]$DefaultScheme = 'http'
    )

    if (-not $Url) {
        return $null
    }

    $trimmed = $Url.TrimEnd('/')
    if ($trimmed -match '^[a-zA-Z][a-zA-Z0-9+.-]*://') {
        return $trimmed
    }

    return "${DefaultScheme}://$trimmed"
}

$backendScript = Join-Path $PSScriptRoot 'fastapi_server.py'
if (-not (Test-Path $backendScript)) {
    throw "Cannot find fastapi_server.py in $PSScriptRoot. Run this script from the repository root."
}

if (-not (Test-Path $PythonPath)) {
    Write-Host "Specified python path '$PythonPath' not found. Falling back to system python executable." -ForegroundColor Yellow
    $PythonPath = 'python'
}

$logDirectory = Join-Path $PSScriptRoot 'logs'
if (-not (Test-Path $logDirectory)) {
    [void][System.IO.Directory]::CreateDirectory($logDirectory)
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$stdoutLogPath = Join-Path $logDirectory "fastapi_backend_$timestamp.out.log"
$stderrLogPath = Join-Path $logDirectory "fastapi_backend_$timestamp.err.log"

$normalizedBackendHost = Normalize-Url -Url $BackendHost
$healthUrl = "$normalizedBackendHost/health"

Write-Host "Starting FastAPI backend with $PythonPath..." -ForegroundColor Cyan
try {
    $backendProcess = Start-Process -FilePath $PythonPath -ArgumentList $backendScript -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutLogPath -RedirectStandardError $stderrLogPath -PassThru
} catch {
    throw "Failed to start backend: $($_.Exception.Message)"
}

Write-Host "Backend PID: $($backendProcess.Id)" -ForegroundColor Green
Write-Host "Backend logs streaming to:`n  STDOUT: $stdoutLogPath`n  STDERR: $stderrLogPath" -ForegroundColor Green

$maxAttempts = 30
$delaySeconds = 1

Write-Host "Waiting for backend health check at $healthUrl ..." -ForegroundColor Cyan
$healthOk = $false
for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    if ($backendProcess.HasExited) {
        $logTail = ''
        if (Test-Path $stdoutLogPath) {
            $logTail += "STDOUT:`n" + (Get-Content $stdoutLogPath -TotalCount 20 | Out-String) + "`n"
        }
        if (Test-Path $stderrLogPath) {
            $logTail += "STDERR:`n" + (Get-Content $stderrLogPath -TotalCount 20 | Out-String)
        }
        throw "Backend process terminated while waiting for health check. Review logs at:`n  $stdoutLogPath`n  $stderrLogPath`n$logTail"
    }

    try {
        $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            $healthOk = $true
            break
        }
    } catch {
        # Ignore transient errors while waiting
    }
    Start-Sleep -Seconds $delaySeconds
}

if (-not $healthOk) {
    Write-Host "Backend did not respond healthy within $maxAttempts seconds. Check logs for details." -ForegroundColor Yellow
} else {
    Write-Host "Backend is healthy." -ForegroundColor Green
}

$frontendProcess = $null
$frontendReady = $false

try {
    $frontendUri = [Uri](Normalize-Url -Url $FrontendUrl)
} catch {
    $frontendUri = [Uri]'http://localhost:5173'
}

if ($StartFrontend.IsPresent) {
    $frontendDir = Join-Path $PSScriptRoot 'web1'
    if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) {
        Write-Host "Could not find web1/package.json. Skipping frontend startup." -ForegroundColor Yellow
    } else {
        $frontendStdout = Join-Path $logDirectory "frontend_dev_$timestamp.out.log"
        $frontendStderr = Join-Path $logDirectory "frontend_dev_$timestamp.err.log"
        $npmCommand = ('set "VITE_BACKEND_URL={0}" && npm run dev' -f $normalizedBackendHost)

        Write-Host "Starting frontend dev server with npm run dev (port $($frontendUri.Port))..." -ForegroundColor Cyan
        try {
            $frontendProcess = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $npmCommand -WorkingDirectory $frontendDir -WindowStyle Hidden -RedirectStandardOutput $frontendStdout -RedirectStandardError $frontendStderr -PassThru
            Write-Host "Frontend dev server PID: $($frontendProcess.Id)" -ForegroundColor Green

            $frontendHealthUrl = $frontendUri.GetLeftPart([System.UriPartial]::Authority)
            if ([string]::IsNullOrEmpty($frontendHealthUrl)) {
                $frontendHealthUrl = 'http://localhost:5173'
            }

            Write-Host "Waiting for frontend dev server at $frontendHealthUrl ..." -ForegroundColor Cyan
            for ($attempt = 1; $attempt -le 60; $attempt++) {
                if ($frontendProcess.HasExited) {
                    Write-Host "Frontend process exited unexpectedly. Check logs:`n  STDOUT: $frontendStdout`n  STDERR: $frontendStderr" -ForegroundColor Yellow
                    break
                }
                try {
                    $response = Invoke-WebRequest -Uri $frontendHealthUrl -UseBasicParsing -TimeoutSec 3
                    if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                        $frontendReady = $true
                        Write-Host "Frontend dev server is ready." -ForegroundColor Green
                        break
                    }
                } catch {
                    # wait and retry
                }
                Start-Sleep -Seconds 1
            }
            if (-not $frontendReady) {
                Write-Host "Frontend dev server did not respond after waiting. You may need to start it manually." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Failed to start frontend dev server: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

$targetUrl = $frontendUri.AbsoluteUri
if (-not $StartFrontend.IsPresent) {
    $targetUrl = Normalize-Url -Url $FrontendUrl
}

Write-Host "Opening browser to $targetUrl" -ForegroundColor Cyan
Start-Process $targetUrl

Write-Host "Backend PID: $($backendProcess.Id). Use Stop-Process -Id $($backendProcess.Id) to stop it." -ForegroundColor Yellow
if ($frontendProcess) {
    Write-Host "Frontend PID: $($frontendProcess.Id). Use Stop-Process -Id $($frontendProcess.Id) to stop it." -ForegroundColor Yellow
}
