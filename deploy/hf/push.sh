#!/usr/bin/env bash
# Publish the current working tree to a Hugging Face Space.
#
#   HF_TOKEN=hf_xxx ./deploy/hf/push.sh <username>/<space-name>
#
# Only git-tracked files are published, so gitignored local state (data/,
# chroma_db/, .env) never leaves the machine. The Space card in
# deploy/hf/SPACE_README.md replaces README.md on the Space side, which keeps
# the YAML front matter Spaces requires out of the GitHub README.
set -euo pipefail

SPACE="${1:-${HF_SPACE:-}}"
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"

if [ -z "$SPACE" ]; then
    echo "usage: HF_TOKEN=hf_xxx $0 <username>/<space-name>" >&2
    exit 1
fi

if [ -z "${HF_TOKEN:-}" ]; then
    echo "FATAL: HF_TOKEN is not set." >&2
    echo "Create a write token at https://huggingface.co/settings/tokens" >&2
    exit 1
fi

if ! git -C "$REPO_ROOT" diff --quiet || ! git -C "$REPO_ROOT" diff --cached --quiet; then
    echo "note: working tree has uncommitted changes; publishing them as-is."
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "cloning Space $SPACE"
git clone "https://user:${HF_TOKEN}@huggingface.co/spaces/${SPACE}" "$WORKDIR/space"

# Clear the Space's tracked files so deletions on our side propagate, then
# repopulate from the working tree.
find "$WORKDIR/space" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +

echo "copying tracked files"
git -C "$REPO_ROOT" ls-files -z | while IFS= read -r -d '' f; do
    mkdir -p "$WORKDIR/space/$(dirname "$f")"
    cp -p "$REPO_ROOT/$f" "$WORKDIR/space/$f"
done

# Space card replaces the GitHub README.
cp "$REPO_ROOT/deploy/hf/SPACE_README.md" "$WORKDIR/space/README.md"

cd "$WORKDIR/space"
git add -A

if git diff --cached --quiet; then
    echo "no changes to publish"
    exit 0
fi

git -c user.email="deploy@localhost" -c user.name="archivist-deploy" \
    commit -q -m "Deploy from $(git -C "$REPO_ROOT" rev-parse --short HEAD)"

# A Space created empty has no branch yet; name it explicitly on first push.
branch="$(git symbolic-ref --quiet --short HEAD || echo main)"
git push origin "HEAD:refs/heads/${branch}"
echo "published to https://huggingface.co/spaces/${SPACE}"
