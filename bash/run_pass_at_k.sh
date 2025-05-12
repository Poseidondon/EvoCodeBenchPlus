model=oracle

python evaluate/testing.py\
    --tests experiments/tests/$model.json\
    --output experiments/pass_at_k/$model.jsonl\
    -k 1
