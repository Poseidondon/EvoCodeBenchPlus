model=racg/without_context/deepseek-coder-6.7b-base_greedy

python evaluate/testing.py\
    --tests experiments/tests/$model.json\
    --output experiments/pass_at_k/$model.jsonl\
    -k 1
