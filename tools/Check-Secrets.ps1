<#
.SYNOPSIS
    Pre-push scan for unsanitized secrets and public IP addresses.

.DESCRIPTION
    Scans every file Git would commit (tracked + untracked, minus anything in
    .gitignore) for:
      - Cisco passwords / secrets / keys / SNMP communities
      - API keys, tokens, private-key blocks
      - Public IPv4 addresses (anything outside RFC 1918, RFC 5737,
        loopback, link-local, CGNAT, multicast, masks and wildcards)

    A line is treated as sanitized if it contains <REDACTED, ChangeMe,
    CHANGE_ME, a ${VAR} / {{ var }} placeholder, os.getenv, or the inline
    marker "sanitize-ok".

    Router-ID style addresses where all four octets match (1.1.1.1, 2.2.2.2)
    are allowed because they're standard lab loopbacks.

    Exits with code 1 if anything is found, so it can gate a push.

.EXAMPLE
    .\tools\Check-Secrets.ps1
.EXAMPLE
    .\tools\Check-Secrets.ps1 -Path .\005-ospf-multiarea
#>
[CmdletBinding()]
param(
    [string]$Path
)

$ErrorActionPreference = 'Stop'
# Default = repo root (parent of tools/). Set here, not in param(), because
# $PSScriptRoot is empty in param defaults under Windows PowerShell 5.1 -File.
if (-not $Path) { $Path = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path) }
$Path = (Resolve-Path $Path).Path

# --- Lines matching this are considered already sanitized -------------------
$allow = '<REDACTED|ChangeMe|CHANGE_ME|\$\{|\{\{|os\.getenv|os\.environ|getenv\(|sanitize-ok'

# --- Secret patterns (most are anchored to line start = config syntax) -------
$secretRules = [ordered]@{
    'Cisco password/secret' = '^\s*(enable\s+(secret|password)|username\s+\S+.*\b(secret|password)|password)\s+(\d\s+)?\S+'
    'Key / PSK'             = '^\s*(crypto\s+isakmp\s+key|key-string|pre-shared-key|(ip\s+ospf\s+)?authentication-key|(ip\s+ospf\s+)?message-digest-key\s+\d+\s+md5|key\s+\d)\s+\S+'
    'SNMP community / v3'   = '^\s*snmp-server\s+(community\s+\S+|user\s+.*\bauth\s+(md5|sha)\s+\S+)'
    'Credential assignment' = '(?i)\b(api[_-]?key|token|secret|passwd|password)\b\s*[:=]\s*["'']?[^\s"'',)]{4,}'
    'Private key block'     = '-----BEGIN [A-Z ]*PRIVATE KEY-----'
    'GitHub token'          = '\bgh[pousr]_[A-Za-z0-9]{20,}'
    'AWS access key'        = '\bAKIA[0-9A-Z]{16}\b'
}

$ipRegex = '\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b'

function Test-PublicIPv4 {
    param([string]$Ip)
    $o = $Ip.Split('.') | ForEach-Object { [int]$_ }
    if ($o[0] -eq 0)                                         { return $false } # wildcards / default route
    if ($o[0] -eq 10)                                        { return $false } # RFC 1918
    if ($o[0] -eq 100 -and $o[1] -ge 64 -and $o[1] -le 127)  { return $false } # CGNAT
    if ($o[0] -eq 127)                                       { return $false } # loopback
    if ($o[0] -eq 169 -and $o[1] -eq 254)                    { return $false } # link-local
    if ($o[0] -eq 172 -and $o[1] -ge 16 -and $o[1] -le 31)   { return $false } # RFC 1918
    if ($o[0] -eq 192 -and $o[1] -eq 168)                    { return $false } # RFC 1918
    if ($o[0] -eq 192 -and $o[1] -eq 0 -and $o[2] -eq 2)     { return $false } # RFC 5737 TEST-NET-1
    if ($o[0] -eq 198 -and $o[1] -eq 51 -and $o[2] -eq 100)  { return $false } # RFC 5737 TEST-NET-2
    if ($o[0] -eq 203 -and $o[1] -eq 0 -and $o[2] -eq 113)   { return $false } # RFC 5737 TEST-NET-3
    if ($o[0] -eq 198 -and $o[1] -ge 18 -and $o[1] -le 19)   { return $false } # RFC 2544 benchmarking
    if ($o[0] -ge 224)                                       { return $false } # multicast, masks, class E
    if (($o | Select-Object -Unique).Count -eq 1)            { return $false } # 1.1.1.1-style router IDs
    return $true
}

# --- Build file list --------------------------------------------------------
$selfPath = $PSCommandPath
if (Test-Path (Join-Path $Path '.git')) {
    $files = git -C $Path -c core.quotepath=off ls-files -co --exclude-standard |
        ForEach-Object { Join-Path $Path $_ }
} else {
    Write-Host "(not a git repo yet - scanning all files)" -ForegroundColor DarkGray
    $files = Get-ChildItem -Path $Path -Recurse -File -Force |
        Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' } |
        ForEach-Object { $_.FullName }
}

$findings = New-Object System.Collections.Generic.List[object]

foreach ($file in $files) {
    if (-not (Test-Path -LiteralPath $file)) { continue }
    if ($file -eq $selfPath -or (Split-Path $file -Leaf) -eq '.gitignore') { continue }

    # Skip binary files (.pkt, images, etc.) — look for a NUL byte
    $bytes = [System.IO.File]::ReadAllBytes($file)
    $probe = [Math]::Min($bytes.Length, 8000)
    if ($probe -gt 0 -and ([Array]::IndexOf($bytes, [byte]0, 0, $probe) -ge 0)) { continue }

    $rel   = $file.Substring($Path.Length).TrimStart('\', '/')
    $lines = [System.IO.File]::ReadAllLines($file)

    for ($i = 0; $i -lt $lines.Length; $i++) {
        $line = $lines[$i]
        if ($line -match $allow) { continue }

        foreach ($rule in $secretRules.GetEnumerator()) {
            if ($line -match $rule.Value) {
                $findings.Add([pscustomobject]@{ File = $rel; Line = $i + 1; Issue = $rule.Key; Text = $line.Trim() })
            }
        }
        foreach ($m in [regex]::Matches($line, $ipRegex)) {
            if (Test-PublicIPv4 $m.Value) {
                $findings.Add([pscustomobject]@{ File = $rel; Line = $i + 1; Issue = "Public IP $($m.Value)"; Text = $line.Trim() })
            }
        }
    }
}

# --- Report -----------------------------------------------------------------
if ($findings.Count -eq 0) {
    Write-Host "OK - no unsanitized secrets or public IPs found in $($files.Count) files." -ForegroundColor Green
    exit 0
}

Write-Host "FOUND $($findings.Count) possible issue(s):`n" -ForegroundColor Red
$findings | Format-Table -AutoSize -Wrap File, Line, Issue, Text
Write-Host "Fix: replace with <REDACTED> / RFC 5737 IPs, or append 'sanitize-ok' if it's intentional." -ForegroundColor Yellow
exit 1
