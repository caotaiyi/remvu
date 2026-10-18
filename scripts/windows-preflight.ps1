# Read-only prerequisites. Does not collect credentials, logs or configuration.
$ErrorActionPreference = 'Stop'
$tools = @{}
foreach ($name in @('git', 'python', 'py', 'claude', 'codex', 'code')) {
    $tools[$name] = [bool](Get-Command $name -ErrorAction SilentlyContinue)
}
[ordered]@{
    purpose = 'Remvu beta prerequisites; not a native-client acceptance result'
    os = [System.Environment]::OSVersion.VersionString
    architecture = $env:PROCESSOR_ARCHITECTURE
    toolsFound = $tools
    nextSteps = @(
        'Use Python 3.10+ from python.org and Git from git-scm.com if missing.',
        'Sign into Claude Code and Codex normally. Do not send keys or passwords.',
        'Open local Code projects in the desktop apps and official VS Code extensions.',
        'Do not grant trust to a future hook definition yet; review the exact installed definition later.',
        'Native acceptance follows docs/native-acceptance.md after the new package is ready.'
    )
} | ConvertTo-Json -Depth 5
