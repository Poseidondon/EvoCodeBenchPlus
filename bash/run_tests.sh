model=racg/context/deepseek-coder-33b

python run_tests.py\
    --tasks dataset/data/oracle.jsonl\
    --completions experiments/completions/$model/completion.jsonl\
    --tests experiments/tests/$model.json\
    --logs experiments/.logs\
    -k 1\
    -r
