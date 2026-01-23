import pandas as pd
import pygmt
import os
import math
import numpy as np
import argparse
from shapely.geometry import Point, LineString
from pathlib import Path
import xml.etree.ElementTree as ET


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth.
    Args:
        lat1, lon1: Latitude and longitude of point 1 in decimal degrees.
        lat2, lon2: Latitude and longitude of point 2 in decimal degrees.
    Returns:
        Distance in kilometers.
    """
    R = 6371.0  # Radius of the Earth in kilometers
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def parse_ruptjson(file):
    """
    Parse a JSON file containing rupture data.
    Args:
        file: Path to the JSON file.
    Returns:
        x and y arrays of coordinates.
    """
    import json

    # Read the JSON file
    print(f"Parsing rupture geometry from {file}")
    with open(file, 'r') as f:
        data = json.load(f)
    # Navigate to the coordinates array
    coordinates = data["features"][0]["geometry"]["coordinates"]
    corners = coordinates[0][0]  # First polygon, first ring

    length = haversine(corners[0][1], corners[0][0], corners[1][1], corners[1][0])
    depth = corners[2][2] - corners[0][2]  
    # Extract the x and y coordinates from the corners
    x = [corners[0][0], corners[1][0], corners[2][0], corners[3][0], corners[4][0]]
    y = [corners[0][1], corners[1][1], corners[2][1], corners[3][1], corners[4][1]]
    print(f'length: {str(length)}')
    print(f'depth: {str(depth)}')
    return x, y

def parse_ruptquads(file):
    """
    Parse a rupt_quads.txt file containing rupture plane realization geometries (produced by ShakeMap)
    Args:
        file: Path to the ruptquads.txt file.
    Returns:
        Pandas dataframe with corners of ruptures
    """
    ruptures = []  # List to store all ruptures
    current_rupture = []  # Temporary list to store points for the current rupture

    with open(file, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("#Origin"):
                # Start of a new rupture, reset the current rupture
                current_rupture = []
            elif line == ">":
                # End of the current rupture, process and store it
                if len(current_rupture) == 5:  # Ensure there are 5 points
                    rupture = {
                        "p1": current_rupture[0],
                        "p2": current_rupture[1],
                        "p3": current_rupture[2],
                        "p4": current_rupture[3],
                    }
                    ruptures.append(rupture)
                current_rupture = []  # Reset for the next rupture
            elif line:
                # Parse a point (lat, lon, depth)
                point = tuple(map(float, line.split()))
                current_rupture.append(point)
    data = []
    for idx, rupture in enumerate(ruptures):
        data.append({
            "rupture_id": idx + 1,
            "p1_lat": rupture["p1"][0], "p1_lon": rupture["p1"][1], "p1_depth": rupture["p1"][2],
            "p2_lat": rupture["p2"][0], "p2_lon": rupture["p2"][1], "p2_depth": rupture["p2"][2],
            "p3_lat": rupture["p3"][0], "p3_lon": rupture["p3"][1], "p3_depth": rupture["p3"][2],
            "p4_lat": rupture["p4"][0], "p4_lon": rupture["p4"][1], "p4_depth": rupture["p4"][2],
        })
    
    return pd.DataFrame(data)

def parse_im_json(file):
    """
    Parse a JSON file containing intensity measure data produced by ShakeMap.
    e.g., cont_mmi.json, cont_pga.json, cont_pgv.json, etc. 
    Args:
        file: Path to the JSON file.
    Returns:
        Geodataframe with IM data. Ready to plot in PyGMT
    """
    import json
    from shapely.geometry import shape
    import geopandas as gpd

    # Read the JSON file
    print(f"Parsing intensity measure data from {file}")
    with open(file, 'r') as f:
        data = json.load(f)
    # Convert GeoJSON-like dicts to shapely geometries
    # Extract 'value' from each feature's properties
    values = [feature['properties']['value'] for feature in data['features']]
    geoms = [shape(feature['geometry']) for feature in data['features']]
    gdf = gpd.GeoDataFrame({'value': values}, geometry=geoms)
    gdf = gdf.set_crs('epsg:4326')
    
    return gdf

def parse_eventxml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    # Get the attributes from the <earthquake> tag
    lat = float(root.attrib['lat'])
    lon = float(root.attrib['lon'])
    depth = float(root.attrib['depth'])
    return lat, lon, depth


def calc_thingbaijam(M):
    """
    Calculate the fault length, width, and area based on the moment magnitude (M).
    """
    # Calc legnth
    b = 0.583
    a = -2.412
    length = 10 ** (a + b*M)

    # Calc width
    b = 0.366
    a = -0.880
    width = 10 ** (a + b*M)

    # Calc area
    b = 0.949
    a = -3.292
    area = 10 ** (a + b*M)

    return length, width, area

