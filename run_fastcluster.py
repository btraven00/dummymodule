#!/usr/bin/env python

"""
Omnibenchmark-izes Markek Gagolewski's https://github.com/gagolews/clustering-results-v1/blob/eae7cc00e1f62f93bd1c3dc2ce112fda61e57b58/.devel/do_benchmark_fastcluster.py
"""

import argparse
import os, sys
import fastcluster
import numpy as np
import scipy.cluster.hierarchy

VALID_LINKAGE = ['complete', 'average', 'weighted', 'median', 'ward', 'centroid']

def load_dataset(data_file):
    data = np.loadtxt(data_file, ndmin=2)

    ##data.reset_index(drop=True,inplace=True)
    
    if data.ndim != 2:
        raise ValueError("Invalid data structure, not a 2D matrix?")

    return(data)

## author Marek Gagolewski
## https://github.com/gagolews/clustering-results-v1/blob/eae7cc00e1f62f93bd1c3dc2ce112fda61e57b58/.devel/do_benchmark_fastcluster.py#L33C1-L58C15
def do_benchmark_fastcluster(X, k, linkage):
    res = dict()
    #for K in Ks: res[K] = dict()
    # method = "fastcluster_%s"%linkage

    # print(" >:", end="", flush=True)

    if linkage in ["median", "ward", "centroid"]:
        linkage_matrix = fastcluster.linkage_vector(X, method=linkage)
    else: # these compute the whole distance matrix
        linkage_matrix = fastcluster.linkage(X, method=linkage)

    # print(".", end="", flush=True)

    # correction for the departures from ultrametricity -- cut_tree needs this.
    linkage_matrix[:,2] = np.maximum.accumulate(linkage_matrix[:,2])
    labels_pred_matrix = scipy.cluster.hierarchy.\
        cut_tree(linkage_matrix, n_clusters=k)+1 # 0-based -> 1-based!!!
    
    res = labels_pred_matrix[:k]

    # print(":<", end="", flush=True)
    return res

def main():
    parser = argparse.ArgumentParser(description='clustbench fastcluster runner')

    parser.add_argument('--data_matrix', type=str,
                        help='gz-compressed textfile containing the comma-separated data to be clustered.', required = True)
    parser.add_argument('--k', type=int,
                        help='k.', required = True)
    parser.add_argument('--output_dir', type=str,
                        help='output directory to store data files.', default=os.getcwd())
    parser.add_argument('--name', type=str, help='name of this module', default='fastcluster')
    parser.add_argument('--linkage', type=str,
                        help='fastcluster linkage',
                        required = True)

    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    if args.linkage not in VALID_LINKAGE:
        raise ValueError(f"Invalid linkage `{args.linkage}`")
    
    curr = do_benchmark_fastcluster(X= load_dataset(args.data_matrix), k = args.k, linkage = args.linkage)

    name = args.name
    
    np.savetxt(os.path.join(args.output_dir, f"{name}.labels.gz"), curr.astype(int), fmt='%i', delimiter=",")
 

if __name__ == "__main__":
    main()
