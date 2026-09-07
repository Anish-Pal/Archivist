#!/usr/bin/env bash
# Publish a branch of this repository to a Hugging Face Space.
#
#   HF_TOKEN=hf_xxx ./deploy/hf/push.sh <username>/<space-name> [source-ref]
#
# source-ref defaults to the branch currently checked out, so running this from
# deploy/hf-spaces publishes that branch rather than main. The ref is exported
# with `git archive`, meaning only committed, git-tracked content is published:
# gitignored local state (.env, data/, chroma_db/) never leaves the machine, and
# uncommitted edits are not deployed.
#
# Spaces always build from their own `main` branch, so whichever source ref is
# chosen is pushed into the Space's main. Override with HF_SPACE_BRANCH.
#
# The Space card in deploy/hf/SPACE_README.md replaces README.md on the Space
# side, which keeps the YAML front matter Spaces requires out of the GitHub
# README.
set -euo pipefail

SPACE="${1:-${HF_SPACE:-}}"
REPO_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
SPACE_BRANCH="${HF_SPACE_BRANCH:-main}"

if [ -z "$SPACE" ]; then
    echo "usage: HF_TOKEN=hf_xxx $0 <username>/<space-name> [source-ref]" >&2
    exit 1
fi

if [ -z "${HF_TOKEN:-}" ]; then
    echo "FATAL: HF_TOKEN is not set." >&2
    echo "Create a write token at https://huggingface.co/settings/tokens" >&2
    exit 1
fi

SOURCE_REF="${2:-${HF_SOURCE_REF:-$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)}}"

if ! git -C "$REPO_ROOT" rev-parse --verify --quiet "${SOURCE_REF}^{commit}" >/dev/null; then
    echo "FATAL: '$SOURCE_REF' is not a commit in this repository." >&2
    exit 1
fi

SOURCE_SHA="$(git -C "$REPO_ROOT" rev-parse --short "$SOURCE_REF")"
echo "source:   $SOURCE_REF ($SOURCE_SHA)"
echo "target:   $SPACE (branch $SPACE_BRANCH)"

# Only committed content ships, so flag anything that would be left behind.
if ! git -C "$REPO_ROOT" diff --quiet HEAD -- 2>/dev/null; then
    echo "WARNING: the working tree has uncommitted changes." >&2
    echo "WARNING: they are NOT published; $SOURCE_REF is deployed as committed." >&2
fi

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "cloning Space"
git clone --quiet "https://user:${HF_TOKEN}@huggingface.co/spaces/${SPACE}" "$WORKDIR/space"

# Clear tracked files so deletions on our side propagate, then repopulate from
# the chosen ref.
find "$WORKDIR/space" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +

echo "exporting $SOURCE_REF"
git -C "$REPO_ROOT" archive --format=tar "$SOURCE_REF" | tar -x -C "$WORKDIR/space"

# Space card replaces the GitHub README.
cp "$WORKDIR/space/deploy/hf/SPACE_README.md" "$WORKDIR/space/README.md"

cd "$WORKDIR/space"
git add -A

if git diff --cached --quiet; then
    echo "no changes to publish"
    exit 0
fi

git -c user.email="deploy@localhost" -c user.name="archivist-deploy" \
    commit -q -m "Deploy ${SOURCE_REF} (${SOURCE_SHA})"

git push origin "HEAD:refs/heads/${SPACE_BRANCH}"
echo "published to https://huggingface.co/spaces/${SPACE}"
