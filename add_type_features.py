import sys
from os import listdir

dataset_folder = sys.argv[1]
output_folder = sys.argv[2]

types_list = []
entity_types = {}

with open(f"datasets/{dataset_folder}/entities.txt", "r") as f:
    for line in f:
        ent, _, _, _, typ = line.strip().split("\t")

        if typ != "?" and typ not in types_list:
            types_list.append(typ)
        entity_types[ent] = typ

def get_type_vec(ent):
    return [1 if entity_types[ent] == typ else 0 for typ in types_list]

def get_header():
    return [f"type1_{typ}" for typ in types_list] + [f"type2_{typ}" for typ in types_list]

for folder in ("test", "train"):
    for ctx in listdir(f"output/{output_folder}/{folder}"):
        for file in listdir(f"output/{output_folder}/{folder}/{ctx}"):
            lines_new = []
            file_path = f"output/{output_folder}/{folder}/{ctx}/{file}"

            with open(file_path, "r") as f:
                for i, line in enumerate(f):
                    triple, label, *feats = line.strip().split(";")

                    if i == 0:
                        to_add = get_header()
                    else:
                        s, _, o = triple.split(",")
                        to_add = get_type_vec(s) + get_type_vec(o)

                    lines_new.append(f"{triple};{label};{';'.join(str(x) for x in to_add)};{';'.join(str(x) for x in feats)}\n")

            with open(file_path, "w") as f:
                f.writelines(lines_new)