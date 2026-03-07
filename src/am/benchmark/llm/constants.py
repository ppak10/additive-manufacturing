DATASET_NAME = "ppak10/Additive-Manufacturing-Benchmark"
EVALUATOR_MODEL = "all-MiniLM-L6-v2"
RUBRIC_EVALUATOR_MODEL = "cross-encoder/nli-deberta-v3-large"
MAX_NEW_TOKENS_SHORT_ANSWER = 4096
MAX_NEW_TOKENS_MELT_POOL = 1024
MAX_NEW_TOKENS_MULTIPLE_CHOICE = 256
TASKS = [
    "general_knowledge_multiple_choice",
    "general_knowledge_short_answer",
    "melt_pool_geometry_prediction",
]
