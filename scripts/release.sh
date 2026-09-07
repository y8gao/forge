#!/usr/bin/env bash
# Forge local release preparation and explicitly authorized commit/tag.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="$REPO_ROOT/VERSION"
CODEX_MANIFEST="$REPO_ROOT/plugins/forge/.codex-plugin/plugin.json"
CLAUDE_MANIFEST="$REPO_ROOT/plugins/forge/.claude-plugin/plugin.json"
CURSOR_MANIFEST="$REPO_ROOT/plugins/forge/.cursor-plugin/plugin.json"
PI_MANIFEST="$REPO_ROOT/package.json"
DSH_MANIFEST="$REPO_ROOT/packages/deepseek-harness/package.json"
RECEIPT="$REPO_ROOT/.git/forge-release-receipt.json"
RECEIPT_SEAL="$REPO_ROOT/.git/forge-release-receipt.sha256"
ALLOWLIST=("VERSION" "plugins/forge/.codex-plugin/plugin.json" "plugins/forge/.claude-plugin/plugin.json" "plugins/forge/.cursor-plugin/plugin.json" "package.json" "packages/deepseek-harness/package.json")

usage() {
  echo "usage: $0 prepare <version> | commit <version> --authorized" >&2
  exit 1
}

[[ $# -ge 2 ]] || usage
ACTION="$1"
TARGET_VERSION="$2"
[[ "$TARGET_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || {
  echo "release: version must be x.y.z" >&2
  exit 1
}
TAG="v$TARGET_VERSION"

cd "$REPO_ROOT"

version_gt() {
  python3 - "$1" "$2" <<'PY'
import sys
left = tuple(map(int, sys.argv[1].split('.')))
right = tuple(map(int, sys.argv[2].split('.')))
raise SystemExit(0 if left > right else 1)
PY
}

sha256_file() {
  python3 - "$1" <<'PY'
import hashlib,sys
print(hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest())
PY
}

validate_prepared_state() {
  [[ -f "$RECEIPT" && -f "$RECEIPT_SEAL" ]] || {
    echo "release: preparation receipt or seal is missing" >&2
    return 1
  }
  [[ "$(cat "$RECEIPT_SEAL")" == "$(sha256_file "$RECEIPT")" ]] || {
    echo "release: preparation receipt changed" >&2
    return 1
  }
  python3 scripts/validate_release_receipt.py "$RECEIPT" "$TARGET_VERSION" "$(git rev-parse HEAD)"
}

run_required_checks() {
  if [[ "${FORGE_RELEASE_TESTING:-}" == "1" ]]; then
    python3 plugins/forge/scripts/forge-memory-validate . || return 1
    bash -n scripts/release.sh || return 1
    return
  fi
  python3 scripts/validate-content.py || return 1
  python3 plugins/forge/scripts/forge-memory-validate . || return 1
  python3 -m unittest tests.test_platform_agents tests.test_cursor_package tests.test_portable_hosts tests.test_agent_profiles tests.test_product_scope tests.test_validate_content tests.test_release_receipt || return 1
  FORGE_RELEASE_TESTING=1 python3 -m unittest tests.test_release || return 1
  bash -n scripts/release.sh || return 1
  if command -v claude >/dev/null 2>&1; then
    claude plugin validate . || return 1
    claude plugin validate ./plugins/forge || return 1
  else
    echo "release: Claude CLI unavailable; static package checks passed"
  fi
  if ! command -v codex >/dev/null 2>&1; then
    echo "release: Codex CLI unavailable; static package checks passed"
  fi
}

write_versions() {
  printf '%s\n' "$TARGET_VERSION" > "$VERSION_FILE"
  python3 - "$TARGET_VERSION" "$CODEX_MANIFEST" "$CLAUDE_MANIFEST" "$CURSOR_MANIFEST" "$PI_MANIFEST" "$DSH_MANIFEST" <<'PY'
import json,sys
version = sys.argv[1]
for name in sys.argv[2:]:
    with open(name, encoding='utf-8') as handle:
        data = json.load(handle)
    data['version'] = version
    with open(name, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write('\n')
PY
}

case "$ACTION" in
  prepare)
    [[ $# -eq 2 ]] || usage
    [[ -z "$(git status --porcelain)" ]] || {
      echo "release: prepare requires a clean worktree" >&2
      exit 1
    }
    CURRENT_VERSION="$(cat "$VERSION_FILE")"
    version_gt "$TARGET_VERSION" "$CURRENT_VERSION" || {
      echo "release: target version must be greater than $CURRENT_VERSION" >&2
      exit 1
    }
    git rev-parse -q --verify "refs/tags/$TAG" >/dev/null 2>&1 && {
      echo "release: tag already exists: $TAG" >&2
      exit 1
    }
    git show "HEAD:CHANGELOG.md" | grep -qF "## [$TARGET_VERSION]" || {
      echo "release: committed CHANGELOG entry is missing for $TARGET_VERSION" >&2
      exit 1
    }
    rm -f "$RECEIPT" "$RECEIPT_SEAL"

    run_required_checks
    BASE_HEAD="$(git rev-parse HEAD)"
    BACKUP_DIR="$(mktemp -d)"
    trap 'rm -rf "$BACKUP_DIR"' EXIT
    for path in "${ALLOWLIST[@]}"; do
      mkdir -p "$BACKUP_DIR/$(dirname "$path")"
      cp "$path" "$BACKUP_DIR/$path"
    done

    if ! write_versions || [[ "${FORGE_RELEASE_FAIL_PREPARED_CHECK:-}" == "1" ]] || ! run_required_checks; then
      for path in "${ALLOWLIST[@]}"; do cp "$BACKUP_DIR/$path" "$path"; done
      rm -f "$RECEIPT" "$RECEIPT_SEAL"
      echo "release: prepared-state validation failed; version files restored" >&2
      exit 1
    fi

    mapfile -t CHANGED < <(git status --porcelain | sed -E 's/^.. //' | sort)
    EXPECTED=("${ALLOWLIST[@]}")
    mapfile -t EXPECTED < <(printf '%s\n' "${EXPECTED[@]}" | sort)
    [[ "${CHANGED[*]}" == "${EXPECTED[*]}" ]] || {
      for path in "${ALLOWLIST[@]}"; do cp "$BACKUP_DIR/$path" "$path"; done
      echo "release: prepared diff escaped the release allowlist" >&2
      exit 1
    }

    python3 - "$RECEIPT" "$TARGET_VERSION" "$TAG" "$BASE_HEAD" "$BACKUP_DIR" "${ALLOWLIST[@]}" <<'PY'
import hashlib,json,sys
from datetime import datetime, timezone
receipt,version,tag,head,backup,*paths = sys.argv[1:]
data = {
    'schema_version': 1,
    'version': version,
    'tag': tag,
    'base_head': head,
    'allowlist': paths,
    'pre_sha256': {path: hashlib.sha256(open(f'{backup}/{path}', 'rb').read()).hexdigest() for path in paths},
    'post_sha256': {path: hashlib.sha256(open(path, 'rb').read()).hexdigest() for path in paths},
    'tag_absent': True,
    'prepared_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    'validation': {
      'content': 'passed',
      'memory': 'passed',
      'packaging': 'passed',
      'product_scope': 'passed',
      'release_matrix': 'passed',
      'shell_syntax': 'passed',
      'host_packages_static': 'passed',
    },
}
with open(receipt, 'w', encoding='utf-8') as handle:
    json.dump(data, handle, indent=2, sort_keys=True)
    handle.write('\n')
PY
  sha256_file "$RECEIPT" > "$RECEIPT_SEAL"
    echo "release: prepared $TARGET_VERSION; review the six-file diff, then run:"
    echo "  $0 commit $TARGET_VERSION --authorized"
    ;;

  commit)
    [[ $# -eq 3 && "$3" == "--authorized" ]] || usage
    validate_prepared_state
    [[ "$(cat "$VERSION_FILE")" == "$TARGET_VERSION" ]] || { echo "release: VERSION mismatch" >&2; exit 1; }
    run_required_checks
    if [[ "${FORGE_RELEASE_TESTING:-}" == "1" && "${FORGE_RELEASE_TEST_MUTATE_AFTER_CHECKS:-}" == "1" ]]; then
      printf '0.0.0\n' > "$VERSION_FILE"
    fi
    validate_prepared_state
    git add -- "${ALLOWLIST[@]}"
    git commit -m "release(forge): v$TARGET_VERSION"
    if [[ "${FORGE_RELEASE_FAIL_TAG:-}" == "1" ]] || ! git tag "$TAG"; then
      echo "release: commit created but tag failed; inspect HEAD and retry tag only after verification" >&2
      exit 2
    fi
    rm -f "$RECEIPT" "$RECEIPT_SEAL"
    echo "release: created commit and tag $TAG; push remains a separate user action"
    ;;
  *) usage ;;
esac
