#!/usr/bin/env python

"""
Omnibenchmark-izes Markek Gagolewski's https://github.com/gagolews/clustering-results-v1/blob/eae7cc00e1f62f93bd1c3dc2ce112fda61e57b58/.devel/do_benchmark_fastcluster.py

Takes the true number of clusters into account and outputs a 2D matrix with as many columns as ks tested,
being true number of clusters `k` and tested range `k plusminus 2`
"""

import argparse
import os, sys
import fastcluster
import numpy as np
import scipy.cluster.hierarchy

VALID_LINKAGE = ['complete', 'average', 'weighted', 'median', 'ward', 'centroid']

def load_labels(data_file):
    data = np.loadtxt(data_file, ndmin=1)
    
    if data.ndim != 1:
        raise ValueError("Invalid data structure, not a 1D matrix?")
    
    return(data)

def load_dataset(data_file):
    data = np.loadtxt(data_file, ndmin=2)
    
    ##data.reset_index(drop=True,inplace=True)
    
    if data.ndim != 2:
        raise ValueError("Invalid data structure, not a 2D matrix?")
    
    return(data)

## modified from
## author Marek Gagolewski
## https://github.com/gagolews/clustering-results-v1/blob/eae7cc00e1f62f93bd1c3dc2ce112fda61e57b58/.devel/do_benchmark_fastcluster.py#L33C1-L58C15
def do_benchmark_fastcluster_single_k(X, ks, linkage):
    res = dict()
    
    if linkage in ["median", "ward", "centroid"]:
        linkage_matrix = fastcluster.linkage_vector(X, method=linkage)
    else: # these compute the whole distance matrix
        linkage_matrix = fastcluster.linkage(X, method=linkage)

    # correction for the departures from ultrametricity -- cut_tree needs this.
    linkage_matrix[:,2] = np.maximum.accumulate(linkage_matrix[:,2])
    labels_pred_matrix = scipy.cluster.hierarchy.\
        cut_tree(linkage_matrix, n_clusters=k)+1 # 0-based -> 1-based!!!
    
    res = labels_pred_matrix#[:k]
    
    return res

## modified from
## author Marek Gagolewski
## https://github.com/gagolews/clustering-results-v1/blob/eae7cc00e1f62f93bd1c3dc2ce112fda61e57b58/.devel/do_benchmark_fastcluster.py#L33C1-L58C15
def do_benchmark_fastcluster_range_ks(X, Ks, linkage):
    res = dict()
    for K in Ks: res[K] = dict()
    
    if linkage in ["median", "ward", "centroid"]:
        linkage_matrix = fastcluster.linkage_vector(X, method=linkage)
    else: # these compute the whole distance matrix
        linkage_matrix = fastcluster.linkage(X, method=linkage)
    
    # correction for the departures from ultrametricity -- cut_tree needs this.
    linkage_matrix[:,2] = np.maximum.accumulate(linkage_matrix[:,2])
    res = scipy.cluster.hierarchy.\
        cut_tree(linkage_matrix, n_clusters=Ks)+1 # 0-based -> 1-based!!!

    return res

def main():
    parser = argparse.ArgumentParser(description='clustbench fastcluster runner')

    parser.add_argument('--data.matrix', type=str,
                        help='gz-compressed textfile containing the comma-separated data to be clustered.', required = True)
    parser.add_argument('--data.true_labels', type=str,
                        help='gz-compressed textfile with the true labels; used to select a range of ks.', required = True)
    parser.add_argument('--output_dir', type=str,
                        help='output directory to store data files.')
    parser.add_argument('--name', type=str, help='name of the dataset', default='clustbench')
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

    truth = load_labels(getattr(args, 'data.true_labels'))
    k = int(max(truth)) # true number of clusters
    Ks = [k-2, k-1, k, k+1, k+2] # ks tested, including the true number
    
    data = getattr(args, 'data.matrix')
    curr = do_benchmark_fastcluster_range_ks(X= load_dataset(data), Ks = Ks, linkage = args.linkage)

    name = args.name

    header=['k=%s'%s for s in Ks]


    curr = np.append(np.array(header).reshape(1,5), curr.astype(str), axis=0)
    np.savetxt(os.path.join(args.output_dir, f"{name}_ks_range.labels.gz"),
               curr, fmt='%s', delimiter=",")#,
               # header = ','.join(header)) 

if __name__ == "__main__":
    main()
