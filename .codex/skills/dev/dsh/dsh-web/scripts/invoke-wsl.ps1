#Requires -Version 7.0
[CmdletBinding(DefaultParameterSetName = 'Script')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Distribution,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^/')]
    [string]$LinuxCwd,

    [string]$LinuxPathPrefix = '',

    [Parameter(Mandatory = $true, ParameterSetName = 'Script')]
    [ValidateNotNullOrEmpty()]
    [string]$Script,

    [Parameter(Mandatory = $true, ParameterSetName = 'Check')]
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
if (-not $IsWindows) {
    throw 'Run this helper in Windows PowerShell 7; it launches Windows wsl.exe.'
}

$info = [System.Diagnostics.ProcessStartInfo]::new()
$info.FileName = Join-Path $env:SystemRoot 'System32\wsl.exe'
$info.UseShellExecute = $false
$info.RedirectStandardOutput = $true
$info.RedirectStandardError = $true
$info.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
$info.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)

if ($Check) {
    $Script = @'
set -euo pipefail
test "$(uname -s)" = Linux
test "${WSL_DISTRO_NAME:-}" = "$2"
test "$(pwd -P)" = "$(realpath -- "$1")"
printf 'WSL_DISTRIBUTION=%s\n' "$WSL_DISTRO_NAME"
printf 'WSL_CWD=%s\n' "$(pwd -P)"
printf 'WSL_KERNEL=%s\n' "$(uname -r)"
for tool in git node pnpm; do
    if tool_path=$(command -v "$tool"); then
        printf 'WSL_TOOL_%s=%s\n' "$tool" "$tool_path"
        case "$tool_path" in
            *.exe) printf 'Windows executable is not a WSL development tool: %s\n' "$tool_path" >&2; exit 1 ;;
        esac
        "$tool" --version
    else
        printf 'WSL_TOOL_%s=missing\n' "$tool"
    fi
done
printf 'WSL_CHECK_OK\n'
'@
}
$Script = 'if [ -n "$3" ]; then export PATH="$3:$PATH"; fi' + "`n" + $Script
foreach ($argument in @('-d', $Distribution, '--cd', $LinuxCwd, '--exec', '/bin/bash', '-lc', $Script)) {
    $info.ArgumentList.Add($argument)
}
$info.ArgumentList.Add('dsh-wsl')
$info.ArgumentList.Add($LinuxCwd)
$info.ArgumentList.Add($Distribution)
$info.ArgumentList.Add($LinuxPathPrefix)

$process = [System.Diagnostics.Process]::Start($info)
try {
    $stdout = $process.StandardOutput.ReadToEndAsync()
    $stderr = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()
    if ($stdout.Result.Length -gt 0) { Write-Output $stdout.Result }
    if ($stderr.Result.Length -gt 0) {
        Write-Output 'WSL_STDERR_BEGIN'
        Write-Output $stderr.Result
        Write-Output 'WSL_STDERR_END'
    }
    Write-Output "WSL_EXIT=$($process.ExitCode)"
    if ($process.ExitCode -ne 0) {
        throw "WSL command failed: $($process.ExitCode)"
    }
}
finally {
    $process.Dispose()
}
