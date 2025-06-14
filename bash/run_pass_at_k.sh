model=racg/without_context/CodeLlama-7b-Python-hf/greedy

python evaluate/testing.py\
    --tests experiments/tests/$model.json\
    --output experiments/pass_at_k/$model.jsonl\
    -k 1
