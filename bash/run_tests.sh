python run_tests.py\
    --tasks dataset/data/oracle.jsonl\
    --completions experiments/baseline/local/local_completion/codellama-7b/completion.jsonl\
    --results output/results/completion-codellama-7b.json\
    --logs output/logs\
    -k 1\
    -r
