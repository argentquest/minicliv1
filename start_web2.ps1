param(
    [string]$PythonPath = (Join-Path $PSScriptRoot 'venv' 'Scripts' 'python.exe'),
    [string]$BackendHost = 'http://localhost:8001',
    [string]$FrontendUrl = 'http://localhost:5174',
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

# Use web_backend_v2 directory for the new backend
$backendDir = Join-Path $PSScriptRoot 'web_backend_v2'
$backendScript = Join-Path $backendDir 'api.py'

if (-not (Test-Path $backendScript)) {
    throw "Cannot find api.py in $backendDir. Make sure web_backend_v2 directory exists."
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
$stdoutLogPath = Join-Path $logDirectory "web2_backend_$timestamp.out.log"
$stderrLogPath = Join-Path $logDirectory "web2_backend_$timestamp.err.log"

$normalizedBackendHost = Normalize-Url -Url $BackendHost
$healthUrl = "$normalizedBackendHost/health"

Write-Host "Starting Web2 Backend (web_backend_v2) with $PythonPath..." -ForegroundColor Cyan
Write-Host "Backend will run on: $normalizedBackendHost" -ForegroundColor Green

# Set environment variable for the backend port
$env:PORT = '8001'

try {
    # Start the backend with uvicorn directly for web2
    $uvicornArgs = @(
        '-m', 'uvicorn',
        'api:app',
        '--host', '0.0.0.0',
        '--port', '8001',
        '--reload'
    )
    $backendProcess = Start-Process -FilePath $PythonPath -ArgumentList $uvicornArgs -WorkingDirectory $backendDir -WindowStyle Hidden -RedirectStandardOutput $stdoutLogPath -RedirectStandardError $stderrLogPath -PassThru
} catch {
    throw "Failed to start web2 backend: $($_.Exception.Message)"
}

Write-Host "Web2 Backend PID: $($backendProcess.Id)" -ForegroundColor Green
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
        throw "Web2 backend process terminated while waiting for health check. Review logs at:`n  $stdoutLogPath`n  $stderrLogPath`n$logTail"
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
    Write-Host "Web2 backend did not respond healthy within $maxAttempts seconds. Check logs for details." -ForegroundColor Yellow
} else {
    Write-Host "Web2 backend is healthy." -ForegroundColor Green
}

$frontendProcess = $null
$frontendReady = $false

try {
    $frontendUri = [Uri](Normalize-Url -Url $FrontendUrl)
} catch {
    $frontendUri = [Uri]'http://localhost:5174'
}

if ($StartFrontend.IsPresent) {
    $frontendDir = Join-Path $PSScriptRoot 'web2'
    if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) {
        Write-Host "Could not find web2/package.json. Skipping frontend startup." -ForegroundColor Yellow
    } else {
        $frontendStdout = Join-Path $logDirectory "web2_frontend_$timestamp.out.log"
        $frontendStderr = Join-Path $logDirectory "web2_frontend_$timestamp.err.log"
        
        # Set environment variables for Vite
        $env:VITE_BACKEND_URL = $normalizedBackendHost
        $env:VITE_PORT = '5174'
        
        $npmCommand = 'npm run dev -- --port 5174'

        Write-Host "Starting Web2 frontend dev server (port 5174)..." -ForegroundColor Cyan
        try {
            $frontendProcess = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', $npmCommand -WorkingDirectory $frontendDir -WindowStyle Hidden -RedirectStandardOutput $frontendStdout -RedirectStandardError $frontendStderr -PassThru
            Write-Host "Web2 Frontend dev server PID: $($frontendProcess.Id)" -ForegroundColor Green

            $frontendHealthUrl = $frontendUri.GetLeftPart([System.UriPartial]::Authority)
            if ([string]::IsNullOrEmpty($frontendHealthUrl)) {
                $frontendHealthUrl = 'http://localhost:5174'
            }

            Write-Host "Waiting for Web2 frontend dev server at $frontendHealthUrl ..." -ForegroundColor Cyan
            for ($attempt = 1; $attempt -le 60; $attempt++) {
                if ($frontendProcess.HasExited) {
                    Write-Host "Web2 frontend process exited unexpectedly. Check logs:`n  STDOUT: $frontendStdout`n  STDERR: $frontendStderr" -ForegroundColor Yellow
                    break
                }
                try {
                    $response = Invoke-WebRequest -Uri $frontendHealthUrl -UseBasicParsing -TimeoutSec 3
                    if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                        $frontendReady = $true
                        Write-Host "Web2 frontend dev server is ready." -ForegroundColor Green
                        break
                    }
                } catch {
                    # wait and retry
                }
                Start-Sleep -Seconds 1
            }
            if (-not $frontendReady) {
                Write-Host "Web2 frontend dev server did not respond after waiting. You may need to start it manually." -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Failed to start Web2 frontend dev server: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

$targetUrl = $frontendUri.AbsoluteUri
if (-not $StartFrontend.IsPresent) {
    $targetUrl = Normalize-Url -Url $FrontendUrl
}

Write-Host "Opening browser to WhisperCode Web2 at $targetUrl" -ForegroundColor Cyan
Start-Process $targetUrl

Write-Host "`n=== WhisperCode Web2 Started ===" -ForegroundColor Green
Write-Host "Backend (web_backend_v2): $normalizedBackendHost" -ForegroundColor Green
Write-Host "Frontend (web2): $targetUrl" -ForegroundColor Green
Write-Host "`nTo stop services:" -ForegroundColor Yellow
Write-Host "  Backend PID: $($backendProcess.Id) - Use: Stop-Process -Id $($backendProcess.Id)" -ForegroundColor Yellow
if ($frontendProcess) {
    Write-Host "  Frontend PID: $($frontendProcess.Id) - Use: Stop-Process -Id $($frontendProcess.Id)" -ForegroundColor Yellow
}
Write-Host "`nLogs located in: $logDirectory" -ForegroundColor Cyan