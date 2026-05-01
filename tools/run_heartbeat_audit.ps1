param(
    [string]$Engine = "http://127.0.0.1:9999/",
    [string]$ProjectRoot = "D:\web_sicherheit"
)

$ErrorActionPreference = "Stop"
$tool = Join-Path $ProjectRoot "tools\mycelia_heartbeat_audit.py"
$out = Join-Path $ProjectRoot "docs\heartbeat\heartbeat_audit_signed.json"

python $tool --engine $Engine --project-root $ProjectRoot --json-out $out
exit $LASTEXITCODE
