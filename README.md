# openai-skill-for-academic

Personal Codex skills for academic and research workflows.

Skills are stored under:

```text
skills/<skill-name>
```

Reusable prompts are stored under:

```text
prompts/<prompt-name>.md
```

Current contents:

- `skills/raman-spectrum-plotting`
- `skills/scientific-figure-composer`
- `skills/publish-skill-to-github`
- `prompts/raman-default-prompt-zh.md`
- `prompts/scientific-figure-user-preferences.md`
- `prompts/academic-research-writing-prompts.md`

Use the `publish-skill-to-github` skill after creating or updating a skill so changes are validated, copied here, committed, and pushed when a GitHub remote is configured.

If normal `git push` is blocked by the local network, sync through the GitHub API:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync_to_github_api.ps1
```

Publish a single prompt file into `prompts/` and upload it:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish_prompt.ps1 -PromptPath "E:\path\to\prompt.md"
```

Publish a skill into `skills/`:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\publish-skill-to-github\scripts\publish_skill.ps1 -SkillPath "E:\openai-skill\your-skill-name"
```
