"""
Author: Saravanakumar Shanmugam Sakthivadivel, 2018
Github: https://github.com/codewithsk/graph-cnn.mxnet

The Ohio State University
Graph Convolutional Network

File: utils.py
Description: Utility functions for Graph Convolutional Networks.
             This file has been adapted from https://github.com/tkipf/pygcn
             and modified for MXNet NDArrays.
"""
import numpy as np
import scipy.sparse as sp
import pdb
from mxnet import nd

def encode_onehot(labels):
    classes = set(labels)
    classes_dict = {c: np.identity(len(classes))[i, :] for i, c in
                    enumerate(classes)}
    labels_onehot = np.array(list(map(classes_dict.get, labels)),
                             dtype=np.int32)
    return labels_onehot


def load_data(ctx, path="data/cora/", dataset="cora"):
    """Load citation network dataset (cora only for now)"""
    print('Loading {} dataset...'.format(dataset))

    idx_features_labels = np.genfromtxt("{}{}.content".format(path, dataset),
                                        dtype=np.dtype(str))
    features = sp.csr_matrix(idx_features_labels[:, 1:-1], dtype=np.float32)
    labels = encode_onehot(idx_features_labels[:, -1])

    # build graph
    idx = np.array(idx_features_labels[:, 0], dtype=np.int32)
    idx_map = {j: i for i, j in enumerate(idx)}
    edges_unordered = np.genfromtxt("{}{}.cites".format(path, dataset),
                                    dtype=np.int32)
    edges = np.array(list(map(idx_map.get, edges_unordered.flatten())),
                     dtype=np.int32).reshape(edges_unordered.shape)
    adj = sp.coo_matrix((np.ones(edges.shape[0]), (edges[:, 0], edges[:, 1])),
                        shape=(labels.shape[0], labels.shape[0]),
                        dtype=np.float32)

    # build symmetric adjacency matrix
    adj = adj + adj.T.multiply(adj.T > adj) - adj.multiply(adj.T > adj)

    features = normalize(features)
    adj = normalize(adj + sp.eye(adj.shape[0]))

    idx_train = range(140)
    idx_val = range(200, 500)
    idx_test = range(500, 1500)

    features = nd.array(features.todense(), dtype=np.float64, ctx=ctx)
    labels = nd.array(np.where(labels)[1], dtype=np.float64, ctx=ctx)
    adj = nd.sparse.array(adj, dtype=np.float64, ctx=ctx)

    idx_train = nd.array(idx_train, ctx=ctx)
    idx_val = nd.array(idx_val, ctx=ctx)
    idx_test = nd.array(idx_test, ctx=ctx)

    return adj, features, labels, idx_train, idx_val, idx_test


def normalize(mx):
    """Row-normalize sparse matrix"""
    rowsum = np.array(mx.sum(1))
    r_inv = np.power(rowsum, -1).flatten()
    r_inv[np.isinf(r_inv)] = 0.
    r_mat_inv = sp.diags(r_inv)
    mx = r_mat_inv.dot(mx)
    return mx


def accuracy(output, labels):
    preds = nd.argmax(output, axis=1)
    correct = preds == labels
    correct = correct.sum()
    correct = correct / len(labels)
    return correct.asnumpy().item()
