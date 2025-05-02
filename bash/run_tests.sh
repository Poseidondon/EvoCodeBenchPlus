model=racg/without_context/deepseek-coder-6.7b-base_greedy

python run_tests.py\
    --tasks /home/jovyan/work/diplom/RAGC/data/evocodebench/oracle.jsonl\
    --repos /home/jovyan/work/diplom/RAGC/data/evocodebench/repos/Source_Code\
    --completions experiments/completions/$model/completion.jsonl\
    --tests experiments/tests/$model.json\
    --logs experiments/.logs\
    -k 1\
    -r
