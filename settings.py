from multiprocessing import cpu_count
import sys

N_THREADS = cpu_count() 
DIRECTIONAL_GRAPH = False

try:
    DATASET = sys.argv[1]
except IndexError:
    print("Please provide a dataset as a command line argument")
    sys.exit()

try:
    MAX_CONTEXT_SIZE = int(sys.argv[2])
except IndexError:
    print("Please provide the maximum context size as a command line argument")
    sys.exit()

PATH_TRAIN = f"datasets/{DATASET}/train.txt"
PATH_TEST = f"datasets/{DATASET}/test.txt"
PATH_RELS = f"datasets/{DATASET}/relations.txt"

EMB_METHOD = None
USE_PATHS = True

TRANSFORM_MODEL = "all-distilroberta-v1"
TRANSFORM_DIMS = 768
