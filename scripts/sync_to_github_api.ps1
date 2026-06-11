[CmdletBinding()]
param(
    [string]$Owner,
    [string]$RepositoryName,
    [string]$Branch = "main",
    [string]$GhPath = "C:\Program Files\GitHub CLI\gh.exe",
    [string]$Message = "Sync skills and prompts via GitHub API"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $GhPath)) {
    $ghCommand = Get-Command gh -ErrorAction SilentlyContinue
    if (-not $ghCommand) {
        throw "GitHub CLI was not found. Install gh or pass -GhPath."
    }
    $GhPath = $ghCommand.Source
}

$RepoPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path

if (-not $Owner -or -not $RepositoryName) {
    $origin = (& git -C $RepoPath remote get-url origin 2>$null)
    if ($origin -match "github\.com[:/](?<owner>[^/]+)/(?<repo>[^/]+?)(?:\.git)?$") {
        if (-not $Owner) {
            $Owner = $Matches.owner
        }
        if (-not $RepositoryName) {
            $RepositoryName = $Matches.repo
        }
    }
}

if (-not $Owner) {
    $Owner = "typering"
}
if (-not $RepositoryName) {
    $RepositoryName = "openai-skill-for-academic"
}

$ApiRoot = "repos/$Owner/$RepositoryName"

function Invoke-GhJson {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [object]$Body
    )

    $tempFile = $null
    try {
        $ghArgs = @("api") + $Arguments
        if ($null -ne $Body) {
            $tempFile = New-TemporaryFile
            $jsonBody = $Body | ConvertTo-Json -Depth 100
            $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
            [System.IO.File]::WriteAllText($tempFile.FullName, $jsonBody, $utf8NoBom)
            $ghArgs += @("--input", $tempFile.FullName)
        }

        $output = & $GhPath @ghArgs
        if ($LASTEXITCODE -ne 0) {
            throw "gh api failed: gh $($ghArgs -join ' ')"
        }

        $json = ($output -join "`n").Trim()
        if (-not $json) {
            return $null
        }
        return $json | ConvertFrom-Json
    }
    finally {
        if ($tempFile -and (Test-Path -LiteralPath $tempFile)) {
            Remove-Item -LiteralPath $tempFile -Force
        }
    }
}

& $GhPath auth status | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

$ref = Invoke-GhJson -Arguments @("$ApiRoot/git/ref/heads/$Branch")
$baseCommitSha = $ref.object.sha

$trackedFiles = & git -C $RepoPath ls-files
if ($LASTEXITCODE -ne 0) {
    throw "Unable to list tracked files from git."
}

$treeEntries = @()
foreach ($relativePath in $trackedFiles) {
    if (-not $relativePath) {
        continue
    }

    $filePath = Join-Path $RepoPath ($relativePath -replace "/", "\")
    if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
        throw "Tracked file is missing locally: $relativePath"
    }

    $bytes = [System.IO.File]::ReadAllBytes($filePath)
    $blob = Invoke-GhJson -Arguments @("--method", "POST", "$ApiRoot/git/blobs") -Body @{
        content = [Convert]::ToBase64String($bytes)
        encoding = "base64"
    }

    $treeEntries += @{
        path = $relativePath
        mode = "100644"
        type = "blob"
        sha = $blob.sha
    }
}

$tree = Invoke-GhJson -Arguments @("--method", "POST", "$ApiRoot/git/trees") -Body @{
    tree = $treeEntries
}

$commit = Invoke-GhJson -Arguments @("--method", "POST", "$ApiRoot/git/commits") -Body @{
    message = $Message
    tree = $tree.sha
    parents = @($baseCommitSha)
}

Invoke-GhJson -Arguments @("--method", "PATCH", "$ApiRoot/git/refs/heads/$Branch") -Body @{
    sha = $commit.sha
    force = $false
} | Out-Null

Write-Host "Synced $($treeEntries.Count) tracked files to https://github.com/$Owner/$RepositoryName/tree/$Branch"
Write-Host "Commit: https://github.com/$Owner/$RepositoryName/commit/$($commit.sha)"
