# Install project skills only; uses Git, never Python or execution-policy changes.
param([string]$Project = (Get-Location).Path, [string]$Source = '')
$ErrorActionPreference = 'Stop'
$Project = (Resolve-Path -LiteralPath $Project).Path
$temp = Join-Path ([IO.Path]::GetTempPath()) ('remvu-skill-' + [guid]::NewGuid().ToString('N'))
try {
    if (-not $Source) {
        Get-Command git -ErrorAction Stop | Out-Null
        & git clone --quiet --depth 1 https://github.com/caotaiyi/remvu.git $temp
        if ($LASTEXITCODE -ne 0) { throw 'Could not fetch source. No project files changed.' }
        $Source = $temp
    }
    $skill = Join-Path $Source 'skills/remvu'
    if (-not (Test-Path -LiteralPath (Join-Path $skill 'references/notes.md'))) { throw 'Source lacks the Markdown skill.' }
    foreach ($client in @('.claude', '.agents')) {
        foreach ($part in @($client, "$client/skills", "$client/skills/remvu")) {
            $path = Join-Path $Project $part
            if ((Test-Path -LiteralPath $path) -and ((Get-Item -Force -LiteralPath $path).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Refusing reparse point: $path" }
        }
        if (Test-Path -LiteralPath (Join-Path $Project "$client/skills/remvu")) { throw 'Remvu skill already exists. Preserve it before replacement; no files changed.' }
    }
    foreach ($client in @('.claude', '.agents')) {
        $parent = Join-Path $Project "$client/skills"
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        $target = Join-Path $parent 'remvu'
        New-Item -ItemType Directory -Path $target | Out-Null
        Copy-Item -LiteralPath (Join-Path $skill 'SKILL.md') -Destination $target
        $license = Join-Path $Source 'LICENSE'
        if (Test-Path -LiteralPath $license) { Copy-Item -LiteralPath $license -Destination $target }
        foreach ($component in @('references', 'assets', 'agents')) {
            $path = Join-Path $skill $component
            if (Test-Path -LiteralPath $path) { Copy-Item -Recurse -LiteralPath $path -Destination (Join-Path $target $component) }
        }
    }
    Write-Output 'Installed project skills. No Python or hooks configured. Use /remvu save in Claude Code or $remvu save in Codex; use resume to continue. Open a new session if necessary. Normal client trust still applies.'
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -Recurse -Force -LiteralPath $temp }
}
