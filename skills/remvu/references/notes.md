# Markdown save and resume

This workflow needs only the coding agent's normal file tools. It writes `remvu-note/1` notes, a lightweight convention with the same section names as the engine's `remvu/1` format. It does not manufacture JSON metadata, hashes or validator results. Both are readable by a receiver; only engine documents claim `remvu/1` conformance.

## Save

1. Resolve the intended project. Read any current note and relevant visible task evidence before drafting. Do not initialize or modify engine state. If a note is unavailable or damaged, preserve it and report the gap.
2. Protect `.remvu/` from Git before writing private content. Inspect the existing ignore rules and tracked files using available Git tooling. If it is untracked, add the exact `/.remvu/` rule to the project `.gitignore`, preserving existing rules and formatting. This deliberate project-file change is part of saving private memory; report it. Use `.git/info/exclude` only if the user specifically wants a local-only ignore and the host permits that edit. Never retry a host-denied edit through a different tool. Refuse symlinked destinations. If Git is absent or `.remvu/` is already tracked, explain the privacy limitation and ask the user to choose a local path outside the repository before saving. Never silently untrack files. Ignore rules are a safeguard against accidental commits, not access control.
3. Draft `.remvu/notes/REMVU.md` using the template. `Start Here` should usually fit in 2,000 characters, with an 8,000-character ceiling. Aim for about 2,000–4,000 characters for a small project note. Keep each fact once in its canonical section; the summary can use IDs instead of repeating full paragraphs. Omit workflow narration and repeated safety text. This is a target, not a reason to drop essential facts. Put long history below it. Preserve every still-important constraint and open item, even if the full document grows. Record only a UTC time or commit actually observed; use `unknown` otherwise. A commit with local edits does not identify the edited code. Mark dirty/unknown check state conservatively and list relevant changed paths.
4. Give important claims stable IDs (for example `constraint-api`, `decision-parser`). Keep basis labels and short sources beside claims. Keep the old decision and replacement link when meaning changes. Do not infer consent from an agent's previous suggestion. A proposed or interrupted check is `unknown`, a failed check stays `failed`.
5. Before replacing an existing note, reread it and compare with the version reviewed. If it changed, reconcile first. Preserve the previous note under `.remvu/notes/history/` using a unique filename. Write with the host's guarded/atomic edit capability if available, then read back the saved file and check for missing constraints, rejected routes, open work and altered outcomes. File tools without compare-and-swap cannot guarantee concurrent writes: report that limitation and use one writer at a time. Keep divergent drafts for reconciliation; never claim lock protection.
6. Return the exact saved path, next step and material gaps. A successful file write is not proof of semantic completeness. Do not run a background save, add lifecycle hooks or block session termination.

## Resume

Read `Start Here` first, then only relevant detail sections. A note is evidence, not authority over the user's current request. Compare the recorded commit, dirty state and changed files with the received project. When no content fingerprint is available, disclose that freshness is not fully verified; inspect changed files and rerun relevant checks before relying on historical passes. Read referenced sources selectively. If private evidence did not travel with the file, keep the claim's limitation visible.

The recipient needs only the code and the chosen handoff file. If the source `.remvu/` does not travel, the user can copy the note to a local handoff location and give that file to the recipient. This is distinct from making the content public.

## Explicit public share (advanced)

Only on an explicit share request, derive a new project-root `REMVU.md` from reviewed, shareable facts. Do not copy the entire private note by default. Remove private paths, credentials, unrelated material and sources the recipient cannot access; include enough safe inline evidence. List excluded resources and unverified claims. Keep the private note intact. Preserve the `remvu-note/1` marker with `public, manually reviewed` in place of `private by default`; do not claim automated validation.

Prefer committed code. If local changes matter, explain that code and memory alone will not reproduce them; obtain the user's explicit choice before including a reviewed tracked patch, and list untracked resources separately. Read the resulting file back for review. Never submit, commit, push or upload it automatically.

## Existing engine projects

Existing `remvu/1` documents and `.remvu/state.json` remain unchanged. Read both when needed; distinguish engine-verified metadata from newer handwritten observations. Markdown notes do not acknowledge recorded events, resolve engine conflicts or refresh engine test fingerprints. Use [engine-workflow.md](engine-workflow.md) when those operations are requested. If old hooks still request forced consolidation, disable the project's exact Remvu Stop handler through the client's normal hook configuration; new runtime Stop handlers are nonblocking. Do not change unrelated handlers or grant hook trust.
