import sys
import numpy as np
import operator
from numpy.core.fromnumeric import shape
from get_playlist_data import get_song_features

# Static global variables
FEATURE_KEYS = ['danceability', 'energy', 'key', 'loudness', 'mode', 'speechiness',
                'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo']
FEAT_KEYS_SZ = len(FEATURE_KEYS)
FEATURE_WEIGHTS = [2.2, 4, 0.1, 1.5, 1, 1,
                   1, 1, 1, 4, 3.3]

class Node:
    def __init__(self, index, uri, name, artist, val_lst=[]) -> None:
        self.index = index
        self.uri = uri
        self.name = name
        self.artist = artist
        self.vals = val_lst


class Tree:
    def __init__(self, index):
        self.index = index
        self.branches = set([])
    
    def add(self, branch):
        self.branches.add(branch)
    
    def remove(self, branch):
        if branch in self.branches:
            self.branches.remove(branch)


def print_tree(trees, nodes) -> None:
    index_nodes = {nd.index : nd for nd in nodes}
    for tree in trees.values():
        print("{}. {}  -  {}".format(tree.index, index_nodes[tree.index].name, index_nodes[tree.index].artist))
        for branch in tree.branches:
            print(" ㄴ-- {}. {}  -  {}".format(branch.index, index_nodes[branch.index].name, index_nodes[branch.index].artist))


def get_node_list(usr, client_id, client_secret) -> list:
    features, names = get_song_features(usr, client_id, client_secret)
    node_lst = []
    for i, feature in enumerate(features):
        val_lst = [feature[k] for k in FEATURE_KEYS]
        new_node = Node(i, feature['uri'], names[i][0], names[i][1], val_lst)
        node_lst.append(new_node)

    return node_lst


def apply_weight(arr):
    val_arr = np.tile(np.array(FEATURE_WEIGHTS), (arr.shape[0], 1))
    return arr * val_arr


def make_dist_matrix(nodes) -> np.ndarray:
    node_arr = np.array([np.array(nd.vals) for nd in nodes])
    dist_mtx = []
    for vals in node_arr:
        val_arr = np.tile(np.array(vals), (node_arr.shape[0], 1))
        res_arr = np.absolute(node_arr - val_arr)
        res_arr = apply_weight(res_arr)
        res = np.sum(res_arr, axis=1)
        dist_mtx.append(res)
    
    return np.array(dist_mtx)


def make_min_span_tree(nodes, dist_mtx) -> list:
    ## TODO: Use Prim algorithm to come up with minimum spanning tree
    copy_mtx = np.copy(dist_mtx)
    index_nodes = {nd.index : nd for nd in nodes}
    nodes_undone = list(range(len(nodes)))
    init_node = nodes_undone.pop(0)
    nodes_undone = set(nodes_undone)
    nodes_done = set([init_node])
    copy_mtx[:, init_node] = np.full(copy_mtx.shape[0], float('inf')).T
    
    span_tree = {}
    while nodes_undone:
        min_val = float('inf')
        min_pair = (None, 0)

        # find the minimum branch to take from the current tree
        for cur_index in nodes_done:
            cur_dist_arr = copy_mtx[cur_index]
            if cur_dist_arr[cur_index] == 0:
                cur_dist_arr[cur_index] = float('inf')
            
            min_index = np.argmin(cur_dist_arr)
            if cur_dist_arr[min_index] < min_val:
                min_pair = (cur_index, min_index)
                min_val = cur_dist_arr[min_index]

        start_node = index_nodes[min_pair[0]]
        end_node = index_nodes[min_pair[1]]

        # add minimum findings to span_tree
        start_tree = Tree(start_node.index)
        end_tree = Tree(end_node.index)
        if start_node.index not in span_tree:
            span_tree[start_node.index] = start_tree
        span_tree[start_node.index].add(end_tree)
            
        if end_node.index not in span_tree:
            span_tree[end_node.index] = end_tree
        span_tree[end_node.index].add(start_tree)

        copy_mtx[:, end_node.index] = np.full(copy_mtx.shape[0], float('inf')).T
        nodes_undone.remove(end_node.index)
        nodes_done.add(end_node.index)
    
    print(nodes_undone)
    return span_tree


def tsp_chris(span_tree, dist_mtx) -> list:
    ## TODO: Use christofides algorithm based on the spanning tree
    return span_tree


def generate_mix(usr, client_id, client_secret) -> list:
    nodes = get_node_list(usr, client_id, client_secret)
    dist_mtx = make_dist_matrix(nodes)
    span_tree = make_min_span_tree(nodes, dist_mtx)
    # result = tsp_chris(span_tree, dist_mtx)
    # return result
    print_tree(span_tree, nodes)
    return None


def main() -> None:
    usr = ('Please input user id: ')
    client_id = input('Enter client id: ')
    client_secret = input('Enter client secret passcode: ')
    print(generate_mix(usr, client_id, client_secret))


def test_dist_mtx(dist_mtx) -> None:
    a = 70
    i = 1
    j = 20
    print(dist_mtx[a][i] + dist_mtx[i][j])
    print(dist_mtx[a][j])


if __name__ == "__main__":
    main()

