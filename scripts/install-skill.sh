#!/bin/sh
# Install project skills only. No Python, hooks, client settings or background service.
set -eu
project=${1:-"$PWD"}
[ -d "$project" ] || { echo 'Project directory does not exist.' >&2; exit 1; }
project=$(cd "$project" && pwd -P)
command -v git >/dev/null 2>&1 || { echo 'Git is required to fetch the reviewed skill source.' >&2; exit 1; }
# REMVU_SOURCE allows installation from a reviewed local checkout, including offline.
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT HUP INT TERM
if [ -n "${REMVU_SOURCE:-}" ]; then
  source=$REMVU_SOURCE
else
  git clone --quiet --depth 1 https://github.com/caotaiyi/remvu.git "$work/source"
  source=$work/source
fi
skill=$source/skills/remvu
[ -f "$skill/SKILL.md" ] && [ -f "$skill/references/notes.md" ] || { echo 'Source lacks the Markdown skill. No files changed.' >&2; exit 1; }
for client in .claude .agents; do
  target=$project/$client/skills/remvu
  # Avoid replacing a user skill or following any project adapter symlink.
  for path in "$project/$client" "$project/$client/skills" "$target"; do
    [ ! -L "$path" ] || { echo "Refusing symlink: $path" >&2; exit 1; }
  done
  [ ! -e "$target" ] || { echo "Already installed: $target. Preserve it before replacing; no files changed." >&2; exit 1; }
done
for client in .claude .agents; do
  mkdir -p "$project/$client/skills"
  target=$project/$client/skills/remvu
  mkdir "$target"
  cp "$skill/assets/markdown-skill.md" "$target/SKILL.md"
  [ ! -f "$source/LICENSE" ] || cp "$source/LICENSE" "$target/LICENSE"
  for component in references assets agents; do
    [ ! -d "$skill/$component" ] || cp -R "$skill/$component" "$target/$component"
  done
done
printf '%s\n' 'Installed project skills. No Python or hooks configured.' 'Claude Code: /remvu save or /remvu resume' 'Codex: $remvu save or $remvu resume' 'Open a new session if the client has not discovered the skill. Existing clients still apply normal project trust.'
