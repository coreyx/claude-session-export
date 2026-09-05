<#
.SYNOPSIS
Installs the optional `claude-export` command shim.

.DESCRIPTION
Writes claude-export.cmd (cmd.exe/PowerShell) and claude-export (POSIX
shells, e.g. Git Bash) into ~/.local/bin, each hardcoded to invoke this
clone's cli.py via the `py -3` launcher. ~/.local/bin is a directory many
dev setups already keep on PATH, so this avoids adding a new PATH entry
per tool/clone. Safe to re-run: it overwrites any existing shim files at
that location. Not required for the CLI to work -- `py -3 cli.py <args>`
always works regardless of whether this has been run.
#>

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$cliPath = Join-Path $repoRoot 'cli.py'
if (-not (Test-Path $cliPath)) {
    throw "Could not find cli.py at $cliPath -- run this script from its original location inside the repo."
}

$targetDir = Join-Path $HOME '.local\bin'
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

$cmdShimPath = Join-Path $targetDir 'claude-export.cmd'
$cmdContent = "@echo off`r`npy -3 `"$cliPath`" %*`r`n"
[System.IO.File]::WriteAllText($cmdShimPath, $cmdContent, [System.Text.Encoding]::ASCII)

$bashShimPath = Join-Path $targetDir 'claude-export'
$bashContent = "#!/usr/bin/env bash`nexec py -3 `"$cliPath`" `"`$@`"`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($bashShimPath, $bashContent, $utf8NoBom)

# Prefer Git for Windows' own bash.exe over `bash` resolved from PATH,
# which on Windows commonly resolves to the WSL launcher stub in
# System32 instead (that one fails here since it just relays into WSL).
$gitBashCandidates = @(
    "$env:ProgramFiles\Git\bin\bash.exe",
    "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
)
$bashExe = $gitBashCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $bashExe) {
    $onPathBash = Get-Command bash -ErrorAction SilentlyContinue
    if ($onPathBash -and $onPathBash.Source -notmatch '\\System32\\') {
        $bashExe = $onPathBash.Source
    }
}
if ($bashExe) {
    & $bashExe -c "chmod +x `"$bashShimPath`""
} else {
    Write-Warning "Git Bash not found -- if you use Git Bash, run: chmod +x `"$bashShimPath`""
}

Write-Host "Installed claude-export shims to $targetDir"
Write-Host "  $cmdShimPath"
Write-Host "  $bashShimPath"

$userPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
$onPath = (($userPath -split ';') -contains $targetDir) -or (($env:PATH -split ';') -contains $targetDir)
if ($onPath) {
    Write-Host "$targetDir is already on PATH -- 'claude-export' should work in new shells now."
} else {
    Write-Warning "$targetDir is not on PATH. Add it once with:`n  [Environment]::SetEnvironmentVariable('PATH', [Environment]::GetEnvironmentVariable('PATH','User') + ';$targetDir', 'User')`nThen open a new shell."
}
