[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PromptPath,

    [string]$PromptName,
    [string]$RepoPath = "E:\self-openai-skills\openai-skill-for-academic",
    [string]$Branch = "main",
    [string]$GhPath = "C:\Program Files\GitHub CLI\gh.exe",
    [switch]$NoPush,
    [switch]$NoApiFallback
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & git -C $RepoPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Git command failed: git -C `"$RepoPath`" $($Arguments -join ' ')"
    }
}

function Get-OriginRemote {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $remote = & git -C $RepoPath remote get-url origin 2>$null
        if ($LASTEXITCODE -ne 0) {
            return $null
        }
        return ($remote | Select-Object -First 1)
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

function Invoke-ApiSync {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message,

        [Parameter(Mandatory = $true)]
        [string]$BranchName
    )

    if ($NoApiFallback) {
        return $false
    }

    $syncScript = Join-Path $RepoPath "scripts\sync_to_github_api.ps1"
    if (-not (Test-Path -LiteralPath $syncScript)) {
        Write-Warning "API sync script was not found: $syncScript"
        return $false
    }

    powershell -ExecutionPolicy Bypass -File $syncScript -Branch $BranchName -GhPath $GhPath -Message $Message
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub API sync failed."
    }
    return $true
}

$resolvedPrompt = (Resolve-Path -LiteralPath $PromptPath).Path
if (-not (Test-Path -LiteralPath $resolvedPrompt -PathType Leaf)) {
    throw "PromptPath must point to a file: $PromptPath"
}

if (-not (Test-Path -LiteralPath (Join-Path $RepoPath ".git"))) {
    throw "RepoPath must point to a git repository: $RepoPath"
}

if (-not $PromptName) {
    $PromptName = Split-Path -Leaf $resolvedPrompt
}

if (-not [System.IO.Path]::GetExtension($PromptName)) {
    $PromptName = "$PromptName.md"
}

$promptsRoot = Join-Path $RepoPath "prompts"
$targetPath = Join-Path $promptsRoot $PromptName
New-Item -ItemType Directory -Force -Path $promptsRoot | Out-Null

$promptsRootFull = [System.IO.Path]::GetFullPath($promptsRoot)
$targetFull = [System.IO.Path]::GetFullPath($targetPath)
$expectedPrefix = $promptsRootFull.TrimEnd("\") + "\"
if (-not $targetFull.StartsWith($expectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to write target outside the repository prompts directory: $targetFull"
}

Copy-Item -LiteralPath $resolvedPrompt -Destination $targetPath -Force

$relativeTarget = "prompts/$PromptName"
Invoke-Git -Arguments @("add", "--", $relativeTarget)

$status = (& git -C $RepoPath status --porcelain -- $relativeTarget)
if (-not $status) {
    Write-Host "No changes to publish for prompt: $PromptName"
    exit 0
}

$message = "Update prompt: $PromptName"
Invoke-Git -Arguments @("commit", "-m", $message)

if ($NoPush) {
    Write-Host "Committed locally only because -NoPush was supplied."
    Write-Host "Repository: $RepoPath"
    exit 0
}

$origin = Get-OriginRemote
if (-not $origin) {
    Write-Warning "No origin remote is configured. The prompt was committed locally but not uploaded to GitHub."
    exit 0
}

$currentBranch = (& git -C $RepoPath branch --show-current).Trim()
if (-not $currentBranch) {
    $currentBranch = $Branch
}

$previousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $pushOutput = & git -C $RepoPath push -u origin $currentBranch 2>&1
    $pushExitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $previousErrorActionPreference
}

if ($pushExitCode -eq 0) {
    $pushOutput | ForEach-Object { Write-Host $_ }
    Write-Host "Published prompt '$PromptName' to $origin on branch $currentBranch."
    exit 0
}

Write-Warning "git push failed. Trying GitHub API sync fallback."
$pushOutput | ForEach-Object { Write-Warning $_ }
if (Invoke-ApiSync -Message $message -BranchName $currentBranch) {
    Write-Host "Published prompt '$PromptName' through GitHub API fallback."
    exit 0
}

throw "Prompt was committed locally, but upload did not complete."
