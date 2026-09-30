#!/usr/bin/env bash
set -e

# Extract and calculate next version
LATEST_TAG=$(git tag --sort=-v:refname | head -n 1)

if [ -z "$LATEST_TAG" ]; then
    # Read current version from pyproject.toml as base
    CURRENT_VER=$(python3 -c "import re, pathlib; print(re.search(r'version\s*=\s*\"([^\"]+)\"', pathlib.Path('pyproject.toml').read_text()).group(1))")
    NEW_VER="$CURRENT_VER"
    NEW_TAG="v$NEW_VER"
else
    CURRENT_VER=${LATEST_TAG#v}
    IFS='.' read -ra VER_PARTS <<< "$CURRENT_VER"
    MAJOR=${VER_PARTS[0]:-0}
    MINOR=${VER_PARTS[1]:-1}
    PATCH=${VER_PARTS[2]:-0}

    ACTION="${1:-patch}"
    case "$ACTION" in
        major)
            NEW_VER="$((MAJOR + 1)).0.0"
            ;;
        minor)
            NEW_VER="${MAJOR}.$((MINOR + 1)).0"
            ;;
        patch)
            NEW_VER="${MAJOR}.${MINOR}.$((PATCH + 1))"
            ;;
        v*)
            NEW_VER="${ACTION#v}"
            ;;
        [0-9]*)
            NEW_VER="$ACTION"
            ;;
        *)
            echo "Unknown release action: $ACTION. Use: patch, minor, major, or explicit version (e.g. 0.2.0)"
            exit 1
            ;;
    esac
    NEW_TAG="v$NEW_VER"
fi

echo "Current version: ${LATEST_TAG:-none (base in pyproject: $CURRENT_VER)}"
echo "Target version:  $NEW_TAG"

echo "Running pre-release validation (task check)..."
task check

echo "Validation passed. Bumping pyproject.toml and r/DESCRIPTION..."
python3 - <<EOF
import re
from pathlib import Path

ver = "$NEW_VER"

# Update pyproject.toml
pyproject = Path("pyproject.toml")
if pyproject.exists():
    content = pyproject.read_text(encoding="utf-8")
    new_content = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{ver}"', content, count=1)
    pyproject.write_text(new_content, encoding="utf-8")

# Update r/DESCRIPTION
desc = Path("r/DESCRIPTION")
if desc.exists():
    content = desc.read_text(encoding="utf-8")
    new_content = re.sub(r'Version:\s*[^\n\r]+', f'Version: {ver}', content, count=1)
    desc.write_text(new_content, encoding="utf-8")
EOF

git add pyproject.toml r/DESCRIPTION
if ! git diff --cached --quiet; then
    git commit -m "chore(release): bump version to $NEW_TAG"
fi

echo "Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    echo "Error: Working directory not clean after bumping version."
    exit 1
fi

BRANCH=$(git branch --show-current)
echo "Current branch: $BRANCH"
if [ "$BRANCH" = "main" ]; then
    echo "Pulling latest changes..."
    git pull --rebase origin main
fi

echo "Tagging release $NEW_TAG..."
git tag -a "$NEW_TAG" -m "Release $NEW_TAG"

echo "Pushing atomically..."
git push --atomic origin "$BRANCH" "$NEW_TAG"

echo "Release $NEW_TAG published successfully! GitHub Actions release workflow triggered."
