import numpy as np
import operator
from numpy.core.fromnumeric import shape
from get_playlist_data import get_song_features

# Static global variables
FEATURE_WEIGHTS = {'danceability' : 2.2 ,
                         'energy' : 4 ,
                            'key' : 0.1 ,
                       'loudness' : 1.5 ,
                           'mode' : 1 ,
                    'speechiness' : 1 ,
                   'acousticness' : 1 ,
               'instrumentalness' : 1 ,
                       'liveness' : 1 ,
                        'valence' : 4 ,
                          'tempo' : 3.3
                    }
FEAT_KEYS_SZ = len(FEATURE_WEIGHTS)

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


# prints tree structure with song title and artist
def print_tree(trees, nodes) -> None:
    index_nodes = {nd.index : nd for nd in nodes}
    for tree in trees.values():
        print("{}. {}  -  {}".format(tree.index, index_nodes[tree.index].name, index_nodes[tree.index].artist))
        for branch in tree.branches:
            print(" ㄴ-- {}. {}  -  {}".format(branch.index, index_nodes[branch.index].name, index_nodes[branch.index].artist))


# gets list of nodes
def get_node_list(usr, playlist_no, client_id, client_secret) -> list:
    features, names = get_song_features(usr, playlist_no, client_id, client_secret)
    node_lst = []
    for i, feature in enumerate(features):
        val_lst = [feature[k] for k in FEATURE_WEIGHTS.keys()]
        new_node = Node(i, feature['uri'], names[i][0], names[i][1], val_lst)
        node_lst.append(new_node)

    return node_lst


# applies weight onto the array
def apply_weight(arr):
    val_arr = np.tile(np.array(list(FEATURE_WEIGHTS.values())), (arr.shape[0], 1))
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
    
    sz = len(dist_mtx)
    for i in range(sz):
        dist_mtx[i][i] = float('inf')

    return np.array(dist_mtx)


# implements prim's algorithm to create minimum spanning tree
def make_min_span_tree(nodes, dist_mtx) -> dict:
    nodes_undone = list(range(len(nodes)))
    init_node = nodes_undone.pop(0)
    nodes_undone = set(nodes_undone)
    nodes_done = set([init_node])

    copy_mtx = np.copy(dist_mtx)
    copy_mtx[:, init_node] = np.full(copy_mtx.shape[0], float('inf')).T

    prob = 0
    span_tree = {}
    while nodes_undone:
        min_val = float('inf')
        min_pair = (None, 0)

        # find the minimum branch to take from the current tree
        for cur_index in nodes_done:
            cur_dist_arr = copy_mtx[cur_index]
            min_index = np.argmin(cur_dist_arr)
            if cur_dist_arr[min_index] <= min_val:
                min_pair = (cur_index, min_index)
                min_val = cur_dist_arr[min_index]

        # add minimum findings to span_tree
        if min_pair[0] not in span_tree:
            span_tree[min_pair[0]] = Tree(min_pair[0])
            
        if min_pair[1] not in span_tree:
            span_tree[min_pair[1]] = Tree(min_pair[1])
        
        span_tree[min_pair[0]].add(span_tree[min_pair[1]])
        span_tree[min_pair[1]].add(span_tree[min_pair[0]])

        copy_mtx[:, min_pair[1]] = np.full(copy_mtx.shape[0], float('inf')).T
        nodes_undone.remove(min_pair[1])
        nodes_done.add(min_pair[1])
    
    return span_tree


# perform minimum weight matching on trees
def minimum_match(tree_branches, trees, odd_mtx, mtx_to_tree_ind) -> list:
    pairs = []
    tree_remains = set(trees)
    while tree_remains:
        oddi1, oddi2 = np.unravel_index(np.argmin(odd_mtx, axis=None), odd_mtx.shape)
        m1, m2 = mtx_to_tree_ind[oddi1], mtx_to_tree_ind[oddi2]

        # print(tree_branches[m1])
        # print(tree_branches[m2])
        
        if m1 in tree_branches[m2]:
            odd_mtx[oddi1][oddi2] = float('inf')
            odd_mtx[oddi2][oddi1] = float('inf')
        else:
            odd_mtx[oddi1] = np.full(odd_mtx.shape[0], float('inf'))
            odd_mtx[:, oddi1] = np.full(odd_mtx.shape[1], float('inf')).T
            odd_mtx[oddi2] = np.full(odd_mtx.shape[0], float('inf'))
            odd_mtx[:, oddi2] = np.full(odd_mtx.shape[1], float('inf')).T
            
            pairs.append((mtx_to_tree_ind[oddi1], mtx_to_tree_ind[oddi2]))
            tree_remains.remove(mtx_to_tree_ind[oddi1])
            tree_remains.remove(mtx_to_tree_ind[oddi2])

    return pairs


# build the spanning tree into an Euler graph
def match_odd_pairs(span_tree, dist_mtx) -> list:
    odd_tree = []
    even_tree = []
    odd_mtx = dist_mtx.copy()
    for tree in span_tree.values():
        if len(tree.branches) % 2 != 0:
            # print(tree.index)
            # print([b.index for b in tree.branches])
            odd_tree.append(tree.index)
        else:
            even_tree.append(tree.index)
    
    odd_tree.sort()
    mtx_to_tree_ind = {}
    odd_mtx = np.delete(odd_mtx, even_tree, 0)
    odd_mtx = np.delete(odd_mtx, even_tree, 1)

    # print(odd_tree)

    sz = odd_mtx.shape[0]
    for i in range(sz):
        mtx_to_tree_ind[i] = odd_tree[i]

    # TODO: get rid of pairs that are already linked together
    tree_branches = {ind : set([b.index for b in tree.branches]) for ind, tree in span_tree.items()}
    matched_pairs = minimum_match(tree_branches, odd_tree, odd_mtx, mtx_to_tree_ind)

    for pair in matched_pairs:
        span_tree[pair[0]].add(span_tree[pair[1]])
        span_tree[pair[1]].add(span_tree[pair[0]])
        # print(len(span_tree[pair[0]].branches))
        # print(len(span_tree[pair[1]].branches))

    return span_tree


# check if the following graph is a valid euler graph
def check_euler_graph(trees):
    flag = True
    for tree in trees.values():
        if len(tree.branches) % 2 != 0:
            print("NOT EULER: {}".format(tree.index))
            flag = False
    
    return flag


# implements christofides algorithm using given spanning tree to create appriximate solution
def tsp_chris(span_tree, dist_mtx) -> list:
    span_tree = match_odd_pairs(span_tree, dist_mtx)
    unvisited_trees = set(span_tree.keys())
    start_tree = unvisited_trees.pop()
    euler_path = None

    if not check_euler_graph(span_tree):
        return None

    # traverse the euler graph using DFS to create eulerean path
    stack = [(([start_tree], 1), set([]), (unvisited_trees, len(unvisited_trees)))]
    while stack:
        cur_path_tp, visited_paths, unvisited_tp = stack.pop()
        cur_path, cp_len = cur_path_tp
        unvisited, uv_len = unvisited_tp

        if uv_len < 1:
            euler_path = cur_path
            print("wow much success")
            break
        
        cur_ind = cur_path[-1]

        # print('cur_ind: {}'.format(cur_ind))

        next_trees = list(span_tree[cur_ind].branches)
        for next_tree in next_trees:
            next_ind = next_tree.index
            new_edge = (cur_ind, next_ind)

            # print('  next_ind: {}'.format(next_ind))
            # print('  new_edge: {}'.format(new_edge))
            # print("  cur_path: {}".format(cur_path))
            # print("  visited_paths: {}".format(visited_paths))

            if cp_len < 2 or (next_ind != cur_path[-2] and new_edge not in visited_paths):
                new_path = cur_path.copy()
                new_path_len = cp_len
                new_visited_paths = visited_paths.copy()
                new_unvisited = unvisited.copy()
                new_uv_len = uv_len

                new_path.append(next_ind)
                new_path_len += 1
                new_visited_paths.add(new_edge)
                if next_ind in new_unvisited:
                    new_unvisited.remove(next_ind)
                    new_uv_len -= 1

                # print("    new_path: {}".format(new_path))
                # print("    new visited_paths: {}".format(new_visited_paths))

                stack.append(((new_path, new_path_len), new_visited_paths, (new_unvisited, new_uv_len)))
            
        #     print("")
        
        # print("")
        # print("")

    if euler_path is None:
        return None

    # TODO: remove duplicates from euler path
    result = []
    visited = set([])
    for n in euler_path:
        if n not in visited:
            visited.add(n)
            result.append(n)   

    return result


def generate_mix(usr, playlist_no, client_id, client_secret) -> list:
    nodes = get_node_list(usr, playlist_no, client_id, client_secret)
    dist_mtx = make_dist_matrix(nodes)
    span_tree = make_min_span_tree(nodes, dist_mtx)
    result = tsp_chris(span_tree, dist_mtx)

    return result


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

