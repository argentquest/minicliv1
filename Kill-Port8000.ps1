param(
    [int]$Port = 8000
)

$connections = Get-NetTCPConnection -LocalPort $Port -State Listen,Established -ErrorAction SilentlyContinue

if (-not $connections) {
    Write-Host "No processes found on port $Port."
    return
}

$processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique

foreach ($processId in $processIds) {
    try {
        $proc = Get-Process -Id $processId -ErrorAction Stop
        Write-Host ("Stopping process {0} (PID {1}) on port {2}" -f $proc.ProcessName, $processId, $Port)
        Stop-Process -Id $processId -Force
    } catch {
        Write-Warning ("Could not stop PID {0}: {1}" -f $processId, $_.Exception.Message)
    }
}
