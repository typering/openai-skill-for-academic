---
name: publish-skill-to-github
description: Use this skill when the user asks to publish, upload, sync, back up, or manage Codex skills in GitHub, especially after "写完 skill", "更新 skill", or creating/modifying any SKILL.md. Default to the GitHub repository name openai-skill-for-academic and publish each skill into its own folder under the skills directory.
---

# Publish Skill to GitHub

## Overview

Use this skill as the finishing workflow for Codex skill creation and updates. It validates the skill, copies it into the dedicated `openai-skill-for-academic` repository, commits the change, and pushes when a GitHub remote is configured.

Default repository:

```text
C:\Users\xiezhiyu\Documents\openai-skill-for-academic
```

Default layout:

```text
openai-skill-for-academic/
  skills/
    <skill-name>/
      SKILL.md
      agents/
      scripts/
      references/
      assets/
```

## When to Run

Run this skill whenever:

- A new Codex skill is created.
- An existing skill is updated.
- The user says "写完 skill", "更新 skill", "上传到 GitHub", "同步 skill", or equivalent wording.
- A skill should be backed up into the `openai-skill-for-academic` repository.

If the current task is skill creation or skill improvement and the user has asked for automatic publishing, treat this as the closing step before the final response.

## Workflow

1. Identify the skill directory. It must contain `SKILL.md`.
2. Validate the skill with `quick_validate.py` before publishing.
3. Ensure the local repository exists at `C:\Users\xiezhiyu\Documents\openai-skill-for-academic`.
4. Copy the skill into `skills/<skill-name>` inside that repository.
5. Validate the copied skill again from the repository location.
6. Commit the change with a message like `Update skill: <skill-name>`.
7. Push only when an `origin` remote is configured, or when the user provides a remote URL.
8. If no remote exists, do not claim the skill was uploaded. Report that it was committed locally and provide the exact `git remote add origin ...` command pattern.

## Script

Use `scripts/publish_skill.ps1` for the repeatable path:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\xiezhiyu\.codex\skills\publish-skill-to-github\scripts\publish_skill.ps1" `
  -SkillPath "C:\Users\xiezhiyu\.codex\skills\raman-spectrum-plotting"
```

Optional parameters:

- `-RepoPath`: override the local `openai-skill-for-academic` repository path.
- `-RemoteUrl`: add `origin` if the repository does not already have one.
- `-NoPush`: commit locally but skip pushing.
- `-SkipValidation`: only for emergency recovery; avoid in normal work.

## Rules

- Never skip validation unless the user explicitly accepts that risk.
- Never overwrite unrelated repositories; the default repo directory name must be `openai-skill-for-academic`.
- Do not push if the repository has no `origin` remote and no `-RemoteUrl` was provided.
- If `git push` fails, say that the local commit exists but upload did not complete.
- Keep skill publishing commits focused on skill files and repository support files.
