# EvoCodeBenchPlus

To address the limitations of DevEval, we build upon EvoCodeBench, a
predecessor framework that shares core architectural features but differs in labeling
format and dataset scale. Although EvoCodeBench includes fewer repositories, its
codebase is largely compatible with DevEval, making it a suitable foundation for
our enhancements. The majority of our development and validation efforts were
carried out using the EvoCodeBench dataset, as described below.

## Problem diagnosis
To verify the correctness of the benchmark evaluation
pipeline, we developed an oracle completion script that injects reference code
directly into the EvoCodeBench format. An ideal benchmark should yield a pass@1
of 1.0 on such oracle completions - signifying that all tests pass when the groundtruth implementation is used. Surprisingly, our initial evaluation produced pass@1
= 0.0. Upon inspection, we discovered that subprocesses responsible for executing
tests were failing due to improperly configured environments—specifically, missing
environment variables that were not propagated to the forked processes. After
resolving this issue, a re-run yielded pass@1 = 0.3636, still far from the expected
result. The lack of any logging around test execution made root-cause analysis
particularly challenging.

## Codebase refactoring
To improve observability and reliability, we refactored the original test execution logic with a focus on transparency and debuggability. Our revised script logs critical runtime details, including:
- The return code from pytest
- Generated junitxml reports
- Standard output and standard error streams from the test subprocess
These logs enabled a more thorough error analysis, revealing that a primary cause
of failure was broken or incomplete virtual environments (venvs) across many
repositories. To address this, we implemented an automated setup script that
iterates through all repositories and attempts to install dependencies into isolated
environments. While this succeeded for the majority of cases, some environments
remained broken due to unsatisfiable dependencies. Rather than fixing these
manually - an approach that is both time-intensive and non-scalable - we chose to
exclude such repositories from the final dataset.

## Dataset refinement
Even after fixing the environment issues, the pass@1
score on oracle completions remained below 1.0. We concluded that this was likely
due to either missing dependencies or flawed test cases. To ensure the integrity of
the benchmark, we filtered out test cases that failed on oracle completions. After
this curation step, we achieved the expected pass@1 = 1.0 for oracle completions -
confirming the validity of the updated evaluation pipeline.

## Docker

Use a pre-built image; building locally is not recommended (venv/oracle setup can fail for some repos).  
**TODO:** Pre-built container link: [TBD].

Pull the image, then from the repo root:

```bash
IMAGE=evocodebench  # or your registry path
bash bash/docker_run_full.sh
```

The script mounts `./experiments` into the container. It runs `run_tests.py` (tasks = `data-success.jsonl` in image, completions from `experiments/completions/oracle/oracle.jsonl`) then `evaluate/testing.py` for pass@k. Outputs: `experiments/tests/oracle-results.json`, `experiments/pass_at_k/oracle.json`, `experiments/.logs/`.

Env overrides: `IMAGE`, `TASKS`, `COMPLETIONS`, `TESTS_JSON`, `LOGS_DIR`, `PASSATK_JSON`, `K_VALUES`. Extra args go to `run_tests.py`.

```bash
COMPLETIONS=experiments/completions/my_model.jsonl K_VALUES="1 5 10" bash bash/docker_run_full.sh
```
