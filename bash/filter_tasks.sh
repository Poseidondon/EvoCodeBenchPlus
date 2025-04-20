python filter_tasks.py\
    --tasks dataset/data/success.jsonl\
    --tests experiments/tests/racg/without_context/codelamma-7b.json\
    --allowed-codes 1 2 3 4 5\
    --output dataset/data/racg-errors.jsonl\
