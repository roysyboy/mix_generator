import sys
import numpy as np
from numpy.core.fromnumeric import shape
from get_user_pl import get_song_features

# Static global variables
FEATURE_KEYS = ['danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
                'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
FEAT_KEYS_SZ = len(FEATURE_KEYS)
FEATURE_WEIGHTS = [1.2, 1.5, 0.1, 1.3, 1, 1, 1, 1, 1, 1, 2.0]

class Node:
    def __init__(self, uri, name, val_lst=[]) -> None:
        self.uri = uri
        self.name = name
        self.vals = val_lst


def get_node_list() -> list:
    features, names = get_song_features()
    node_lst = []
    for i, feature in enumerate(features):
        val_lst = [feature[k] for k in FEATURE_KEYS]
        new_node = Node(feature['uri'], names[i], val_lst)
        node_lst.append(new_node)

    return node_lst


def apply_weight(arr):
    val_arr = np.tile(np.array(FEATURE_WEIGHTS), (arr.shape[0], 1))
    return arr * val_arr


def make_dist_matrix(nodes) -> list:
    node_arr = np.array([np.array(nd.vals) for nd in nodes])
    # print(node_arr.shape)
    dist_mtx = []
    for vals in node_arr:
        val_arr = np.tile(np.array(vals), (node_arr.shape[0], 1))
        res_arr = np.absolute(node_arr - val_arr)
        res_arr = apply_weight(res_arr)
        res = np.sum(res_arr, axis = 1)
        dist_mtx.append(res)
    
    return dist_mtx


def make_spanning_tree(nodes, dist_mtx) -> list:
    ## TODO: Use Prim algorithm to come up with minimum spanning tree
    return nodes


def tsp_chris(span_tree, dist_mtx) -> list:
    ## TODO: Use christofides algorithm based on the spanning tree
    return span_tree


def main() -> None:
    usr = ('Please input user id: ')
    nodes = get_node_list(usr)
    dist_mtx = make_dist_matrix(nodes)

    test(nodes, dist_mtx)

    span_tree = make_spanning_tree(nodes, dist_mtx)
    result = tsp_chris(span_tree, dist_mtx)
    print(result)


def test(nodes, dist_mtx) -> None:
    a = 70
    i = 1
    j = 20
    print(dist_mtx[a][i] + dist_mtx[i][j])
    print(dist_mtx[a][j])


if __name__ == "__main__":
    main()

