model=baseline/without_context/codellama-7b

python evaluate/testing.py\
    --tests experiments/tests/$model.json\
    --output experiments/pass_at_k/$model.jsonl\
    -k 1 3 5 10
