"""
This code is pretty much just a copy of the example from 
https://osmnx.readthedocs.io/en/stable/
"""

# -*- coding: utf-8 -*-

#from keys import google_elevation_api_key #replace this with your own API key
import osmnx as ox, networkx as nx, numpy as np
import scipy as sp
from scipy.io import savemat

import csv

lat = 46.9868
long = 12.1825
distance = 8000  # Distance (meters) from the starting point along the network 
road_type = "bike"  # drive, drive_service, walk, bike, all, all_private

G = ox.graph_from_point((lat,long), distance=distance, network_type=road_type)


# Get position of each node
keys = ["row_num"]  # # Get keys
nodes = []  # Get nodes
for node in G.nodes:
    nodes.append(node)
    for key in G.nodes.get(node).keys():
        if(not key in keys):
            keys.append(key)

# Export positions data
with open("node_pos.csv","w",newline='') as f:
    wr = csv.writer(f)
    wr.writerow(keys)
    count = 1
    for node in G.nodes:
        row = {"row":count}
        row.update(G.nodes.get(node))
        w = csv.DictWriter(f,row.keys())
        w.writerow(row)
        count += 1


# Get adjacency matrix from the graph
A = nx.adjacency_matrix(G)
# Add weights
w,h = A.get_shape()
for i in range(w):
    for j in range(h):
        if(A[i,j] == 1):
            A[i,j] = G.get_edge_data(nodes[i],nodes[j])[0]["length"]

#sp.sparse.save_npz('sparse_matrix.npz', A)
savemat('temp', {'M':A})

