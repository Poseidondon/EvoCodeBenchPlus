#!/bin/bash
set -e 

IMAGE="${IMAGE:-konstfed/evocodebenchplus}"
# Paths inside container (under /app)
TASKS="${TASKS:-dataset/data/data-success.jsonl}"
# local path to completions
COMPLETIONS="${COMPLETIONS:-experiments/completions/oracle/oracle.jsonl}"
# local path to save results of tests
TESTS_JSON="${TESTS_JSON:-experiments/tests/oracle-results.json}"
# local path to save logs
LOGS_DIR="${LOGS_DIR:-experiments/.logs}"
# local path to save results of pass@k
PASSATK_JSON="${PASSATK_JSON:-experiments/pass_at_k/oracle.json}"
# k values to set 
# K_VALUES="${K_VALUES:-1 5 10}"
K_VALUES="${K_VALUES:-1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EXPERIMENTS_ABS="$REPO_ROOT/experiments"
mkdir -p "$EXPERIMENTS_ABS"
VOLUME_MOUNT="$EXPERIMENTS_ABS:/app/experiments"
# Repos: use /app/dataset/repos inside image (no host mount)

echo "Using image: $IMAGE"
echo "Mount experiments: $VOLUME_MOUNT"
echo "Repos: from image (/app/dataset/repos)"
echo "Completions: $COMPLETIONS"
echo "Tests output: $TESTS_JSON"
echo "Pass@k output: $PASSATK_JSON"
echo "---"

echo "Step 1/2: run_tests.py"
docker run --rm \
  -v "$VOLUME_MOUNT" \
  --entrypoint python \
  "$IMAGE" \
  "run_tests.py" \
  "-j 8" \
  -t "$TASKS" \
  -c "$COMPLETIONS" \
  --tests "$TESTS_JSON" \
  -l "$LOGS_DIR" \
  "$@"

echo ""
echo "Step 2/2: evaluate/testing.py (pass@k)"
docker run --rm \
  -v "$VOLUME_MOUNT" \
  --entrypoint python \
  "$IMAGE" \
  evaluate/testing.py \
  --tests "$TESTS_JSON" \
  --output "$PASSATK_JSON" \
  -k $K_VALUES

echo ""
echo "Done. Results on host:"
echo "  tests:    $REPO_ROOT/experiments/tests/$(basename "$TESTS_JSON")"
echo "  pass@k:   $REPO_ROOT/experiments/pass_at_k/$(basename "$PASSATK_JSON")"
echo "  logs:     $REPO_ROOT/experiments/.logs/"
