python run_tests.py\
    --tasks dataset/data/oracle.jsonl\
    --completions experiments/baseline/without_context/codellama-13b/completion.jsonl\
    --results output/results/baseline/naive-codellama-13b\
    --logs output/logs\
    -k 1\
    -r
