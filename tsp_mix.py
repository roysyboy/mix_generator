import numpy as np
import operator
from numpy.core.fromnumeric import shape
from get_playlist_data import get_song_features, uri_to_playlist, get_playlist

# static global variables
FEATURE_WEIGHTS = {'danceability' : 15 ,    # [0, 1]
                         'energy' : 10 ,    # [0, 1]
                            'key' : 0 ,
                       'loudness' : 5 ,     # (-60, 0)
                           'mode' : 0 ,
                    'speechiness' : 0 ,
                   'acousticness' : 8 ,     # [0, 1]
               'instrumentalness' : 4 ,     # [0, 1]
                       'liveness' : 0.5 ,   # [0, 1]
                        'valence' : 10 ,    # [0, 1]
                          'tempo' : 15      # BPM
                    }
FEAT_KEYS_SZ = len(FEATURE_WEIGHTS)

# Node is a song/track represents as a node used to create distance matrix between each node
class Node:
    def __init__(self, index, uri, name, artist, val_lst=[]) -> None:
        self.index = index
        self.uri = uri
        self.name = name
        self.artist = artist
        self.vals = val_lst

# Tree represents a node from the tree structure used to generate minimum spanning tree
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
    features, names, playlist_name = get_song_features(usr, playlist_no, client_id, client_secret)
    node_lst = []
    for i, feature in enumerate(features):
        val_lst = [feature[k] for k in FEATURE_WEIGHTS.keys()]
        new_node = Node(i, feature['uri'], names[i][0], names[i][1], val_lst)
        node_lst.append(new_node)

    return node_lst, playlist_name


# applies weight onto the array
def apply_weight(arr):
    val_arr = np.tile(np.array(list(FEATURE_WEIGHTS.values())), (arr.shape[0], 1))
    return arr * val_arr


# create 2x2 distance matrix of each nodes
def make_dist_matrix(nodes) -> np.ndarray:
    node_arr = np.array([np.array(nd.vals) for nd in nodes])
    dist_mtx = []
    for vals in node_arr:
        val_arr = np.tile(np.array(vals), (node_arr.shape[0], 1))
        res_arr = apply_weight(np.absolute(node_arr - val_arr))
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


# perform minimum weight matching onto given nodes
def minimum_match(tree_branches, trees, odd_mtx, mtx_to_tree_ind) -> list:
    pairs = []
    tree_remains = set(trees)
    while tree_remains:
        oddi1, oddi2 = np.unravel_index(np.argmin(odd_mtx, axis=None), odd_mtx.shape)
        m1, m2 = mtx_to_tree_ind[oddi1], mtx_to_tree_ind[oddi2]
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


# build Euler graph by pairing nodes of spanning trees with odd number of vertices
def match_odd_pairs(span_tree, dist_mtx) -> list:
    odd_tree = []
    even_tree = []
    odd_mtx = dist_mtx.copy()

    # filter out nodes with degree of odd and even numbers
    for tree in span_tree.values():
        if len(tree.branches) % 2 != 0:
            odd_tree.append(tree.index)
        else:
            even_tree.append(tree.index)
    
    odd_tree.sort()
    mtx_to_tree_ind = {}

    # create distance matrix only containing nodes with degree of odd number 
    odd_mtx = np.delete(odd_mtx, even_tree, 0)
    odd_mtx = np.delete(odd_mtx, even_tree, 1)

    sz = odd_mtx.shape[0]
    for i in range(sz):
        mtx_to_tree_ind[i] = odd_tree[i]

    tree_branches = {ind : set([b.index for b in tree.branches]) for ind, tree in span_tree.items()}
    matched_pairs = minimum_match(tree_branches, odd_tree, odd_mtx, mtx_to_tree_ind)

    # add newly paired nodes to the tree
    for pair in matched_pairs:
        span_tree[pair[0]].add(span_tree[pair[1]])
        span_tree[pair[1]].add(span_tree[pair[0]])

    return span_tree


# check if the given graph is a valid euler graph
def check_euler_graph(trees):
    flag = True
    for tree in trees.values():
        if len(tree.branches) % 2 != 0:
            print("NOT EULER: {}".format(tree.index))
            flag = False
    
    return flag


# implements christofides algorithm using given spanning tree to build approiximate solution
def tsp_chris(span_tree, dist_mtx) -> list:
    span_tree = match_odd_pairs(span_tree, dist_mtx)
    unvisited_trees = set(span_tree.keys())
    start_tree = unvisited_trees.pop()
    euler_path = None

    if not check_euler_graph(span_tree):
        return None

    # traverse the euler graph via DFS to create eulerean path
    stack = [(([start_tree], 1), set([]), (unvisited_trees, len(unvisited_trees)))]
    while stack:
        cur_path_tp, visited_paths, unvisited_tp = stack.pop()
        cur_path, cp_len = cur_path_tp
        unvisited, uv_len = unvisited_tp

        if uv_len < 1:
            euler_path = cur_path
            print("Mix successfully created.")
            break
        
        cur_ind = cur_path[-1]

        next_trees = list(span_tree[cur_ind].branches)
        for next_tree in next_trees:
            next_ind = next_tree.index
            new_edge = (cur_ind, next_ind)

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

                stack.append(((new_path, new_path_len), new_visited_paths, (new_unvisited, new_uv_len)))

    if euler_path is None:
        return None

    result = []
    visited = set([])
    
    # remove duplicates from the euler path
    for n in euler_path:
        if n not in visited:
            visited.add(n)
            result.append(n)   

    return result


# build given list of indices into list of uri's
def path_to_uri(nodes, tsp_path) -> list:
    node_dict = {node.index : node.uri for node in nodes}
    uri_list = [node_dict[ind] for ind in tsp_path]

    return uri_list


# build given list of indices into list of track's names and each of its artists
def path_to_name_artist(nodes, tsp_path) -> list:
    node_dict = {node.index : node.name + "  - " + node.artist for node in nodes}
    name_artist_list = [node_dict[ind] for ind in tsp_path]

    return name_artist_list


# print out each track from the given list of tracks and artists
def print_playlist(name_artist_list) -> None:
    for i, track in enumerate(name_artist_list):
        print("{}. {}".format(i + 1, track))


##### mix generator function #####
# build a mix for given playlist of given user
def generate_mix(usr, playlists, playlist_no, client_id, client_secret) -> list:
    
    # get playlist as a list of nodes and generate distance matrix between each node
    nodes, playlist_name = get_node_list(usr, playlist_no, client_id, client_secret)
    dist_mtx = make_dist_matrix(nodes)

    # creates minimum spanning tree (MST)
    span_tree = make_min_span_tree(nodes, dist_mtx)

    # uses christofides algorithm for the given MST
    tsp_path = tsp_chris(span_tree, dist_mtx)

    # creates the new playlist to the user's profile
    uri_list = path_to_uri(nodes, tsp_path)
    uri_to_playlist(uri_list, usr, playlist_name)
    name_artist_list = path_to_name_artist(nodes, tsp_path)

    return name_artist_list


##### main #####
def main() -> None:
    usr = ('Please enter your user id: ')
    client_id = input('Enter client id: ')
    client_secret = input('Enter client secret passcode: ')
    playlists = get_playlist(usr, client_id, client_secret)
    pl_no = ('Please enter number of your playlist: ')
    pl_len = len(playlists)
    while pl_no.isdigit() or (int(pl_no) < 1 or int(pl_no) > pl_len):
        pl_no = ('Please enter number of your playlist: ')

    name_artist_list = generate_mix(usr, playlists, int(pl_no), client_id, client_secret)
    print_playlist(name_artist_list)


if __name__ == "__main__":
    main()

