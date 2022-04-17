from tqdm               import tqdm
from networkx.exception import NodeNotFound
from sentence_transformers import SentenceTransformer

from settings           import N_THREADS, DIRECTIONAL_GRAPH, DATASET, PATH_TRAIN, PATH_TEST, PATH_RELS, MAX_CONTEXT_SIZE
from features           import get_feature_vector, get_header
from utils              import count_file_lines, generate_negatives

from os.path import isfile
import settings
import time

import networkx as nx
from networkx.algorithms.centrality     import degree_centrality

def worker(nproc, emb_dict):

    def _print(*args, **kwargs):
        # Avoid printing the same stuff multiple times
        if nproc == 0:
            print(*args, **kwargs)

    def _regular_iterator(ls):
        for l in ls:
            yield l
    
    iterator = tqdm if nproc == 0 else _regular_iterator

    graph = nx.MultiDiGraph() if DIRECTIONAL_GRAPH else nx.MultiGraph()
    possible_targets = {}
    positive_train_triples = []

    train_lines = count_file_lines(PATH_TRAIN)
    test_lines = count_file_lines(PATH_TEST)

    # Start and end ranges for the triples that this thread will process
    start_range_train = int(nproc * train_lines / N_THREADS)
    end_range_train = int((nproc + 1) * train_lines / N_THREADS)

    start_range_test = int(nproc * test_lines / N_THREADS)
    end_range_test = int((nproc + 1) * test_lines / N_THREADS)

    rels_to_study = None
    rels_study_path = f"datasets/{DATASET}/relations_to_study.txt"
    if isfile(rels_study_path):
        rels_to_study = []
        with open(rels_study_path, "r") as f:
            for line in f:
                if line:
                    rels_to_study.append(line.strip().split("\t")[0])

    # Load the data from the training split
    _print("Loading training data")
    with open(PATH_TRAIN, "r") as f:
        for i, line in enumerate(f):
            spl = line.strip().split("\t")

            # Skip negative examples in the training split, since we generate our own negatives
            if len(spl) >= 4 and spl[3] != "1": continue

            s, r, t = spl[:3]
            if r not in possible_targets:
                possible_targets[r] = []
            possible_targets[r].append(t)
 
            graph.add_edge(s, t, rel=r, key=r)
            if start_range_train <= i < end_range_train and (rels_to_study is None or r in rels_to_study):
                positive_train_triples.append((s, r, t))

    _print("Removing duplicate targets")
    # Remove duplicates from the possible targets dict
    for r, ls in possible_targets.items():
        possible_targets[r] = list(set(ls))

    with open(PATH_RELS, "r") as f:
        relations = [x.strip().split("\t")[0] for x in f.readlines()]

    # Generate the negatives by replacing the target entity with a random one
    # from the same range
    _print("Generating negatives")
    negative_train_triples = generate_negatives(positive_train_triples, possible_targets)
    labelled_triples_train = [((s, r, t, 1), None) for s, r, t in positive_train_triples] + negative_train_triples

    _print("Computing features for the training split")
    training_csv = open(f"output/{DATASET}/train.csv.{nproc}", "a")

    centrality_indices = degree_centrality(graph)

    if not rels_to_study:
        rels_to_study = relations

    transform_model = None
    if settings.TRANSFORM_MODEL:
        transform_model = SentenceTransformer(settings.TRANSFORM_MODEL, device="cpu")

    t1 = time.thread_time()

    
    for (s, r, t, label), orig in iterator(labelled_triples_train):
        fvec = get_feature_vector(graph, (s, r, t), relations, bool(label), orig, emb_dict,
            centrality_indices=centrality_indices, rels_to_study=rels_to_study, transform_model=transform_model)
        training_csv.write(f"{s},{r},{t};{label};{';'.join(str(x) for x in fvec)}\n")

    t2 = time.thread_time()
    training_csv.close()
    

    _print("Loading testing data")
    labelled_triples_test = []
    with open(PATH_TEST, "r") as f:
        for i, line in enumerate(f):
            if start_range_test <= i < end_range_test:
                spl = line.strip().split("\t")
                s, r, t, lbl = spl[:4]
                if rels_to_study is None or r in rels_to_study:
                    labelled_triples_test.append((s, r, t, 1 if lbl == "1" else 0))

    _print("Computing features for the testing split")
    testing_csv = open(f"output/{DATASET}/test.csv.{nproc}", "a")

    t3 = time.thread_time()

    for s, r, t, label in iterator(labelled_triples_test):
        try:
            fvec = get_feature_vector(graph, (s, r, t), relations, emb_dict=emb_dict,
                centrality_indices=centrality_indices, rels_to_study=rels_to_study, transform_model=transform_model)
        except NodeNotFound:
            # Since the testing data does not appear in the training split,
            # an entity present in the testing split may not appear in the
            # graph generated by the training split.
            continue
        testing_csv.write(f"{s},{r},{t};{label};{';'.join(str(x) for x in fvec)}\n")

    t4 = time.thread_time()
    testing_csv.close()

    elapsed_seconds = (t2 - t1) + (t4 - t3)

    with open("compute_times.txt", "a") as f:
        f.write(f"{DATASET};c{MAX_CONTEXT_SIZE};thread{nproc};{elapsed_seconds}\n")