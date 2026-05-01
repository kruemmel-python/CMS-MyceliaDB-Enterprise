param(
    [string]$Engine = "http://127.0.0.1:9999",
    [string[]]$Probe = @(),
    [string[]]$Operation = @("register_user","login_attractor","restore_snapshot"),
    [string]$ChallengeId = "",
    [string]$JsonOut = "strict_cert_v18e.json"
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host "[Mycelia v1.18E] $msg"
}

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not $ChallengeId -or $ChallengeId.Trim() -eq "") {
    $ChallengeId = "v18e-" + [Guid]::NewGuid().ToString("N")
}

if (-not $Probe -or $Probe.Count -eq 0) {
    Write-Warning "Keine --Probe Werte übergeben. Der Probe läuft ohne sensitive Known-Strings und kann Strict-Residency nicht sinnvoll beweisen."
}

$proc = Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -like "*mycelia_platform.py*" } |
    Select-Object -First 1

if (-not $proc) {
    throw "Kein laufender mycelia_platform.py Prozess gefunden."
}

$pidValue = [int]$proc.ProcessId
Write-Step "Engine PID: $pidValue"
Write-Step "Challenge: $ChallengeId"

$probeArgs = @("tools\mycelia_memory_probe.py", "--pid", "$pidValue", "--challenge-id", $ChallengeId, "--json-out", "residency_probe_v18e.json")
foreach ($p in $Probe) {
    $probeArgs += @("--probe", $p)
}
foreach ($op in $Operation) {
    $probeArgs += @("--operation", $op)
}

Write-Step "Starte externen RAM-Probe"
& python @probeArgs
if ($LASTEXITCODE -ne 0) {
    throw "mycelia_memory_probe.py fehlgeschlagen mit ExitCode $LASTEXITCODE"
}

Write-Step "Starte Strict-VRAM-Zertifizierung"
& python tools\mycelia_strict_vram_certify.py --engine $Engine --probe-report residency_probe_v18e.json --json-out $JsonOut
$exit = $LASTEXITCODE
if ($exit -ne 0) {
    Write-Warning "Strict-Zertifizierung wurde nicht erreicht. Prüfe native_gpu_capability_report, latest_external_memory_probe PID und last_restore_cpu_materialized."
}

Write-Step "Report: $JsonOut"
exit $exit
