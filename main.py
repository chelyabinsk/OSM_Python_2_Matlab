#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# anaconda-navigator --reset

from osgeo import gdal  # pip install gdal
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox, geopandas as gpd, networkx as nx, numpy as np
ox.config(log_file=True, log_console=True, use_cache=True)
import scipy as sp
from scipy.io import savemat
import csv
import math

def combine_tif(files):
    global fullmap
    gdal.UseExceptions()
    
    fullmap = 0 
    
    filenum = 0
    
    global x0G
    global y0G
    global dxG
    global dyG
    
    for file in files:    
        ds = gdal.Open('Data/Map Greenwich/' + file)  # TIF elevation file
    
        x0, dx, dxdy, y0, dydx, dy = ds.GetGeoTransform()
        if(filenum == 0):
            x0G = x0
            y0G = y0
            dyG = dy
            dxG = dx
        band = ds.GetRasterBand(1)
        elevation = band.ReadAsArray()
        
        nrows, ncols = elevation.shape
        
        x1 = x0 + dx * ncols  # right corner most X
        y1 = y0 + dy * nrows # lowest most y
        
        if(filenum == 0):
            fullmap = elevation
        elif(filenum == 1):
            fullmap = np.hstack((fullmap,elevation))
        elif(filenum == 2):
            tmpmap = elevation
        elif(filenum == 3):
            tmpmap = np.hstack((tmpmap,elevation))
            fullmap = np.vstack((fullmap,tmpmap))
        
        filenum +=1
    
    # Replace all negative values with 0
    fullmap[fullmap < 0 ] = 0

    plt.imshow(fullmap, cmap='gist_earth')
    plt.show()
    
#files = ["srtm_39_03.tif",
#        "srtm_40_03.tif",
#         "srtm_39_04.tif",
#         "srtm_40_04.tif"]
    
files = ["srtm_36_02.tif",
        "srtm_37_02.tif"]
    
# Check if full heightmap has been created
if not "fullmap" in globals():
    combine_tif(files)

    
def find_closest_corners(pos):
    y,x = pos
    
    # Workout the closest 4 edges in the elevation
    
    nY = math.floor((y-y0G)/dyG)
    
    yTop = y0G + dyG*nY
    yBot = y0G + dyG*(nY+1)
  
    nX = math.floor((x-x0G)/dxG)
    
#    print(y,x,nX,nY)
    
    xLeft = x0G + dxG*nX
    xRight = x0G + dxG*(nX+1)

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
    
    el_TL = fullmap[nY,nX]  # Elevation Top Left
    el_TR = fullmap[nY,nX+1]  # Elevation Top Right
    el_BL = fullmap[nY+1,nX]  # Elevation Bottom Left
    el_BR = fullmap[nY+1,nX+1]  # Elevation Bottom Right
    
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
        height = (
                + (1/d2)*el_TR + (1/d3)*el_BL + (1/d4)*el_BR)/(
                    1/d1 + 1/d2 + 1/d3 + 1/d4)
        
    #return(xL,yT,xR,yB,nX,nY,el_TL,el_TR,el_BL,el_BR,height)
    return height


#{'y': 51.4850659, 'x': 0.0578418, 'osmid': 6150242294}
#print(get_weighted_height((51.4850659,0.0578418)))

# get the boundary polygons for multiple cities, save as shapefile, project to UTM, and plot
#place_names = [
#               {"type":"boundary",
#                "country":"United Kingdom",
#                "state":"Wales",
#                "county":"Newport"},
#                
#                {"type":"boundary",
#                "country":"United Kingdom",
#                "state":"Wales",
#                "county":"Cardiff"},
#                 
#                 {"type":"boundary",
#                "country":"United Kingdom",
#                "state":"Wales",
#                "county":"Vale of Glamorgan"}
#               ]
place_names = [
                #"London Borough of Newham, London, Greater London, England, United Kingdom",
                #"Royal Borough of Lambeth, London, Greater London, England, United Kingdom",
                "Greater London, England, United Kingdom"
               ]

city_buffered = ox.gdf_from_places(place_names, buffer_dist=0)
fig, ax = ox.plot_shape(city_buffered)

G = ox.graph_from_place(place_names, network_type='bike')
ox.plot_graph(G)

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
print("Exporting matlab thing")
# Get adjacency matrix from the graph
A = nx.adjacency_matrix(G)
# Add weights
w,h = A.get_shape()
nz = A.nonzero()
for i in range(len(nz[0])):
    print("{} out of {}. {}%".format(i,len(nz[0]),round(100*i/len(nz[0]),4)) )    
    A[nz[0][i],nz[1][i]] = G.get_edge_data(nodes[nz[0][i]],nodes[nz[1][i]])[0]["length"]

#sp.sparse.save_npz('sparse_matrix.npz', A)
savemat('temp', {'M':A})
