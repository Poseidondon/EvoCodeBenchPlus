model=racg/without_context/CodeLlama-7b-Python-hf/greedy

python run_tests.py\
    --tasks /home/jovyan/work/diplom/EvoCodeBenchPlus/dataset/data/oracle.jsonl\
    --repos /home/jovyan/work/diplom/EvoCodeBenchPlus/dataset/repos\
    --completions experiments/completions/$model.jsonl\
    --tests experiments/tests/$model.json\
    --logs experiments/.logs\
    -k 1\
    -r
