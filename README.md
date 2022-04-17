# SciCheck
Source code for SciCheck, a tool for scientific fact checking in Knowledge Graphs. Currently under review in FGCS.

# How to run SciCheck
- Configure `settings.py` to set whether to use a directional graph or not, and the sentence embedding model to use.
- Include your dataset in the `datasets/` folder.
- Set up the dependencies listed in `requirements.txt`
- Run SciCheck using `python main.py <dataset> <size>`, where `<dataset>` is the name of the dataset's folder, and `<size>` is the maximum number of hops to use when computing features.