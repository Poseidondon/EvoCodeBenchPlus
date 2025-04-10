model=baseline/without_context/codellama-7b

python run_tests.py\
    --tasks dataset/data/oracle.jsonl\
    --completions experiments/completions/$model/completion.jsonl\
    --tests experiments/tests/$model.json\
    --logs experiments/.logs\
    -k 10
