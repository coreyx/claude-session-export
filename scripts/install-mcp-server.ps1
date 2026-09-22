<#
.SYNOPSIS
Installs and registers the claude-session-export MCP server with Claude Code.

.DESCRIPTION
Resolves the python.exe behind `py -3`, installs the `mcp` package for it,
then runs `claude mcp add --scope user` pointing at this clone's
mcp_server.py using that absolute python.exe path (an absolute path is
required for reliable subprocess spawning -- see spec/tech.md for why).
Safe to re-run: if the server is already registered, it's removed and
re-added so its paths stay current (e.g. after moving the repo or
reinstalling Python).
#>

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$serverPath = Join-Path $repoRoot 'mcp_server.py'
$requirementsPath = Join-Path $repoRoot 'requirements.txt'
if (-not (Test-Path $serverPath)) {
    throw "Could not find mcp_server.py at $serverPath -- run this script from its original location inside the repo."
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    throw "The 'claude' CLI was not found on PATH. Install Claude Code first, then re-run this script."
}

Write-Host "Resolving the Python interpreter used by 'py -3'..."
$pythonExe = (& py -3 -c "import sys; print(sys.executable)" 2>$null)
if ($pythonExe) { $pythonExe = $pythonExe.Trim() }
if (-not $pythonExe -or -not (Test-Path $pythonExe)) {
    throw "Could not resolve a python.exe via 'py -3'. Install Python 3.12+ and ensure the 'py' launcher works, then re-run this script."
}
Write-Host "  $pythonExe"

Write-Host "Installing the 'mcp' package for that interpreter..."
& $pythonExe -m pip install -r $requirementsPath
if ($LASTEXITCODE -ne 0) {
    throw "pip install failed (exit $LASTEXITCODE). See the output above."
}

$serverName = 'claude-session-export'
# Redirecting stderr from a native command while $ErrorActionPreference is
# 'Stop' turns that output into a terminating error in PowerShell 5.1, so
# 'claude mcp get' reporting "not found" (expected on a first install) would
# otherwise abort the script instead of just setting a non-zero exit code.
$previousEap = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& claude mcp get $serverName *> $null
$alreadyRegistered = ($LASTEXITCODE -eq 0)
if ($alreadyRegistered) {
    Write-Host "'$serverName' is already registered -- removing it so it can be re-added with current paths..."
    & claude mcp remove $serverName *> $null
}
$ErrorActionPreference = $previousEap

Write-Host "Registering '$serverName' with Claude Code (user scope, available in every project)..."
& claude mcp add --scope user $serverName -- "$pythonExe" "$serverPath"
if ($LASTEXITCODE -ne 0) {
    throw "claude mcp add failed (exit $LASTEXITCODE). See the output above."
}

Write-Host ""
Write-Host "Verifying registration:"
& claude mcp get $serverName

Write-Host ""
Write-Host "Done. MCP servers are only loaded when a Claude Code session starts,"
Write-Host "so start a new session (or restart your current one) to see the new tools."
