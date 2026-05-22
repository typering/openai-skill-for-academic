[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SkillPath,

    [string]$RepoPath = "$env:USERPROFILE\Documents\openai-skill-for-academic",
    [string]$RepositoryName = "openai-skill-for-academic",
    [string]$Branch = "main",
    [string]$ValidatorPath = "E:\openai-skill\.system\skill-creator\scripts\quick_validate.py",
    [string]$GhPath = "C:\Program Files\GitHub CLI\gh.exe",
    [string]$RemoteUrl,
    [switch]$NoPush,
    [switch]$NoApiFallback,
    [switch]$SkipValidation
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

function Invoke-Validation {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if ($SkipValidation) {
        Write-Warning "Skipping skill validation because -SkipValidation was supplied."
        return
    }

    if (-not (Test-Path -LiteralPath $ValidatorPath)) {
        throw "Validator not found: $ValidatorPath"
    }

    $env:PYTHONUTF8 = "1"
    & python $ValidatorPath $Path
    if ($LASTEXITCODE -ne 0) {
        throw "Skill validation failed: $Path"
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

$resolvedSkill = (Resolve-Path -LiteralPath $SkillPath).Path
$skillName = Split-Path -Leaf $resolvedSkill
$skillFile = Join-Path $resolvedSkill "SKILL.md"

if (-not (Test-Path -LiteralPath $skillFile)) {
    throw "SkillPath must point to a skill directory containing SKILL.md: $resolvedSkill"
}

if ((Split-Path -Leaf $RepoPath) -ne $RepositoryName) {
    throw "Repository directory must be named $RepositoryName. Current path: $RepoPath"
}

New-Item -ItemType Directory -Force -Path $RepoPath | Out-Null

if (-not (Test-Path -LiteralPath (Join-Path $RepoPath ".git"))) {
    & git -C $RepoPath init -b $Branch
    if ($LASTEXITCODE -ne 0) {
        & git -C $RepoPath init
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to initialize git repository at $RepoPath"
        }
        Invoke-Git -Arguments @("checkout", "-B", $Branch)
    }
}

$gitUserName = (& git -C $RepoPath config user.name 2>$null)
if (-not $gitUserName) {
    Invoke-Git -Arguments @("config", "user.name", "Codex Skill Publisher")
}

$gitUserEmail = (& git -C $RepoPath config user.email 2>$null)
if (-not $gitUserEmail) {
    Invoke-Git -Arguments @("config", "user.email", "codex-skill-publisher@users.noreply.github.com")
}

$readmePath = Join-Path $RepoPath "README.md"
if (-not (Test-Path -LiteralPath $readmePath)) {
    @"
# openai-skill-for-academic

Personal Codex skills for academic and research workflows.

Skills are stored under `skills/<skill-name>`.
"@ | Set-Content -LiteralPath $readmePath -Encoding UTF8
}

$gitignorePath = Join-Path $RepoPath ".gitignore"
if (-not (Test-Path -LiteralPath $gitignorePath)) {
    @"
__pycache__/
*.pyc
.DS_Store
node_modules/
.pytest_cache/
"@ | Set-Content -LiteralPath $gitignorePath -Encoding UTF8
}

Invoke-Validation -Path $resolvedSkill

$skillsRoot = Join-Path $RepoPath "skills"
$targetPath = Join-Path $skillsRoot $skillName
New-Item -ItemType Directory -Force -Path $skillsRoot | Out-Null

$skillsRootFull = [System.IO.Path]::GetFullPath($skillsRoot)
$targetFull = [System.IO.Path]::GetFullPath($targetPath)
$expectedPrefix = $skillsRootFull.TrimEnd('\') + '\'
if (-not $targetFull.StartsWith($expectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to replace target outside the repository skills directory: $targetFull"
}

if (Test-Path -LiteralPath $targetPath) {
    Remove-Item -LiteralPath $targetPath -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $targetPath | Out-Null

Get-ChildItem -LiteralPath $resolvedSkill -Force | Where-Object {
    $_.Name -notin @(".git", "__pycache__", ".pytest_cache", "node_modules")
} | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $targetPath -Recurse -Force
}

Invoke-Validation -Path $targetPath

if ($RemoteUrl) {
    $existingOrigin = Get-OriginRemote
    if (-not $existingOrigin) {
        Invoke-Git -Arguments @("remote", "add", "origin", $RemoteUrl)
    }
}

Invoke-Git -Arguments @("add", "--", "README.md", ".gitignore", "skills/$skillName")

$status = (& git -C $RepoPath status --porcelain -- "README.md" ".gitignore" "skills/$skillName")
if (-not $status) {
    Write-Host "No changes to publish for skill: $skillName"
    exit 0
}

$commitMessage = "Update skill: $skillName"
Invoke-Git -Arguments @("commit", "-m", $commitMessage)

if ($NoPush) {
    Write-Host "Committed locally only because -NoPush was supplied."
    Write-Host "Repository: $RepoPath"
    exit 0
}

$origin = Get-OriginRemote
if (-not $origin) {
    Write-Warning "No origin remote is configured. The skill was committed locally but not uploaded to GitHub."
    Write-Host "To connect GitHub later, run:"
    Write-Host "git -C `"$RepoPath`" remote add origin https://github.com/<your-username>/$RepositoryName.git"
    Write-Host "git -C `"$RepoPath`" push -u origin $Branch"
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
    Write-Host "Published skill '$skillName' to $origin on branch $currentBranch."
    exit 0
}

Write-Warning "git push failed. Trying GitHub API sync fallback."
$pushOutput | ForEach-Object { Write-Warning $_ }
if (Invoke-ApiSync -Message $commitMessage -BranchName $currentBranch) {
    Write-Host "Published skill '$skillName' through GitHub API fallback."
    exit 0
}

throw "Skill was committed locally, but upload did not complete."
