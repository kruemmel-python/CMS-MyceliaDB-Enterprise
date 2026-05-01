param(
    [string]$ProjectRoot = "D:\web_sicherheit",
    [string]$TaskName = "MyceliaDB Strict VRAM Heartbeat Audit",
    [string]$Engine = "http://127.0.0.1:9999/",
    [string]$At = "03:15"
)

$ErrorActionPreference = "Stop"
$script = Join-Path $ProjectRoot "tools\run_heartbeat_audit.ps1"
if (!(Test-Path $script)) {
    throw "Heartbeat script not found: $script"
}

$argument = "-NoProfile -ExecutionPolicy Bypass -File `"$script`" -ProjectRoot `"$ProjectRoot`" -Engine `"$Engine`""
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argument
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Runs MyceliaDB external CPU-RAM probe and submits signed Strict-VRAM heartbeat evidence." -Force | Out-Null

Write-Host "Scheduled task installed: $TaskName"
Write-Host "ProjectRoot: $ProjectRoot"
Write-Host "Engine: $Engine"
Write-Host "Daily at: $At"
Write-Host "Manual run:"
Write-Host "  powershell -ExecutionPolicy Bypass -File `"$script`" -ProjectRoot `"$ProjectRoot`" -Engine `"$Engine`""
