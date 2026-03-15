DATASET_NAME = "ppak10/Additive-Manufacturing-Benchmark"
PROCTOR_MODEL = "openai/gpt-oss-20b"
MAX_NEW_TOKENS_SHORT_ANSWER = 4096
MAX_NEW_TOKENS_MELT_POOL = 1024
MAX_NEW_TOKENS_MULTIPLE_CHOICE = 256
MAX_NEW_TOKENS_PROCTOR = 512
MAX_NEW_TOKENS_DEFECT_CLASSIFICATION = 128
MAX_NEW_TOKENS_MACHINES = 256
TASKS = [
    "general_knowledge_multiple_choice",
    "general_knowledge_short_answer",
    "melt_pool_geometry_prediction",
    "fdm_3d_printing_defect",
    "machines",
]
