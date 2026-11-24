# Project delivery entry

Fill in verified source/build/test paths before use; do not infer commands from this template.

- Scope and current state: maintain one project status file.
- Small changes: implement and verify the related behavior directly.
- Significant changes: agree observable acceptance, then work in thin slices.
- Keep changes on feature branches; follow the repository PR/merge rules.
- Fast checks: record the actual project command here after verification.
- Release checks: record the actual build and key user journey here.
- Delegation: use installed aipm-delegate only for clear independent tasks; read-only reviews, bounded implementation workspaces; no silent model fallback.
- Record actual evidence, artifact version, limitations and next step. Logs in .aipm/ are local runtime state and should be ignored by Git.
- Load only the relevant installed Skill. Do not preload every Skill or copy the complete library into this file.
