# Codex runner notes

Use the Codex CLI already installed and authenticated by the user. Binary discovery, JSON parsing and session continuation come from Oil. No model request is made by dry-run.

New read tasks: codex exec --sandbox read-only. New implementation tasks: --sandbox workspace-write. Resume retains the corresponding sandbox_mode configuration. This derivative never selects a danger-full-access or bypass flag. Unsupported provider runners fail explicitly.

Requested model and effort are explicit argv values. If the CLI rejects them, return the failure; do not silently use another model. The CLI response's requested-model field is not proof of the backend model. Root validation records may separately verify CLI session metadata; do not infer actual_model from an assistant's self-report.

Missing login/home/permissions is an environment failure. Report it and request only the required approved environment access; do not rewrite HOME or disable the sandbox.

References: https://learn.chatgpt.com/docs/non-interactive-mode and https://github.com/oil-oil/oil-dev-skills .
