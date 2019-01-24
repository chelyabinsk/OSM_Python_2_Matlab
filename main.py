# -*- coding: utf-8 -*-

# Estimate elevation for each node
# I am using weighted average from 4 nearest neighbours

# Code from: https://stackoverflow.com/questions/24956653/read-elevation-using-gdal-python-from-geotiff
from osgeo import gdal  # Elevation data
import matplotlib.pyplot as plt
#from keys import google_elevation_api_key #replace this with your own API key
import osmnx as ox, networkx as nx, numpy as np
import scipy as sp
from scipy.io import savemat
import math
#import elevation  # https://pypi.org/project/elevation/

import csv

lat = 46.9868
long = 12.1825
distance = 8000  # Distance (meters) from the starting point along the network 
road_type = "bike"  # drive, drive_service, walk, bike, all, all_private

gdal.UseExceptions()

ds = gdal.Open('srtm_39_03.tif')  # TIF elevation file
band = ds.GetRasterBand(1)
elevation = band.ReadAsArray()



plt.imshow(elevation, cmap='gist_earth')
plt.show()

nrows, ncols = elevation.shape

# I'm making the assumption that the image isn't rotated/skewed/etc. 
# This is not the correct method in general, but let's ignore that for now
# If dxdy or dydx aren't 0, then this will be incorrect
x0, dx, dxdy, y0, dydx, dy = ds.GetGeoTransform()

x1 = x0 + dx * ncols  # right corner most X
y1 = y0 + dy * nrows  # lowest most y

def find_closest_corners(pos):
    y,x = pos
    
    # Workout the closest 4 edges in the elevation
    
    nY = math.floor((y-y0)/dy)
    
    yTop = y0 + dy*nY
    yBot = y0 + dy*(nY+1)

        
    nX = math.floor((x-x0)/dx)
    
    xLeft = x0 + dx*nX
    xRight = x0 + dx*(nX+1)

    
    return(xLeft,yTop,xRight,yBot,nX,nY)
    
def get_distances(pos,corners):
    # Euclidian distances from point to corners
    y,x = pos
    xL,yT,xR,yB = corners
    dTL = math.sqrt((x-xL)**2+(y-yT)**2)  # Top left distance
    dTR = math.sqrt((x-xR)**2+(y-yT)**2)  # Top right distance
    dBL = math.sqrt((x-xL)**2+(y-yB)**2)  # Bottom left distance
    dBR = math.sqrt((x-xR)**2+(y-yB)**2)  # Bottom right distance
    return(dTL,dTR,dBL,dBR)

def get_weighted_height(pos):
    # left-X, top-Y, right-X, bottom-Y, square_count from left-nX, 
    #   square_count_from_top-nY
    xL,yT,xR,yB,nX,nY = find_closest_corners(pos)
    
    el_TL = elevation[nY,nY]  # Elevation Top Left
    el_TR = elevation[nX+1,nY]  # Elevation Top Right
    el_BL = elevation[nX,nY+1]  # Elevation Bottom Left
    el_BR = elevation[nY+1,nY+1]  # Elevation Bottom Right
    
    # d1   d2
    
    #    pos
    
    # d3   d4
    
    d1,d2,d3,d4 = get_distances(pos,(xL,yT,xR,yB))
    if(d1 == 0):
        height = el_TL
    elif(d2 == 0):
        height = el_TR
    elif(d3 == 0):
        height = el_BL
    elif(d4 == 0):
        height = el_BR
    else:
        height = ((1/d1)*el_TL + (1/d2)*el_TR + (1/d3)*el_BL + (1/d4)*el_BR)/(
                    1/d1 + 1/d2 + 1/d3 + 1/d4)
        
    #return(xL,yT,xR,yB,nX,nY,el_TL,el_TR,el_BL,el_BR,height)
    return height

G = ox.graph_from_point((lat,long), distance=distance, network_type=road_type)

# Get position of each node
keys = ["row_num","alt"]  # # Get keys
nodes = []  # Get nodes
for node in G.nodes:
    nodes.append(node)
    for key in G.nodes.get(node).keys():
        if(not key in keys):
            keys.append(key)

# Export positions data
with open("node_pos_alt.csv","w",newline='') as f:
    wr = csv.writer(f)
    wr.writerow(keys)
    count = 1
    for node in G.nodes:
        row = {"row":count}
        tmp = G.nodes.get(node)
        row.update({"alt":get_weighted_height((tmp["y"],tmp["x"]))})
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
