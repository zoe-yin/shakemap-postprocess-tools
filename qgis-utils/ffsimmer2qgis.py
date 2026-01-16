#!/usr/bin/env python

import pandas as pd
import os
# import math
# import numpy as np
import argparse
# from shapely.geometry import Point, LineString
# from pathlib import Path
import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point



# Parse command line arguments
parser = argparse.ArgumentParser(description="Parse rupt_quads.txt file and write as QGIS-compatile geojson files.")
parser.add_argument('--productdir', type=str, default=None, help='Path to the product directory. The script will look for a file named rupt_quads.txt in this directory. This flag will export the rupture polygons and updip edge lines as GeoJSON files for use in QGIS.')
parser.add_argument('--eventxml', type=str, default=None, help='Path to the event.xml file. The script will look for a file named event.xml in this directory.')

### Example usage: 
# python /Users/hyin/soft/shakemap-postprocess-tools/qgis-utils/ffsimmer2qgis.py --productdir /Users/hyin/shakemap_profiles/default/data/us6000rsy1/np1/products --eventxml /Users/hyin/shakemap_profiles/default/data/us6000rsy1/np1/event.xml


args = parser.parse_args()

file_path = args.productdir

if args.productdir is None:
    # look for rupt_quads.txt in the current directory
    if os.path.isfile('rupt_quads.txt'):
        file_path = '.'
    else:
        parser.error("No product directory provided and rupt_quads.txt not found in the current directory.")


if args.eventxml is None: 
    # look for the xml
    if os.path.isfile('../event.xml'):
        args.eventxml = '../event.xml'
    else:
        print("No event.xml provided and event.xml not found in the parent directory. Epicenter point will not be created.")
        pass

def parse_ruptquads(file):
    '''
    Parse the rupt_quads.txt file and return a DataFrame with rupture information. 
    Each row corresponds to one rupture, with columns for the lat, lon, and depth 
    of each of the 4 points (p1, p2, p3, p4).
    '''
    ruptures = []  # List to store all ruptures
    current_rupture = []  # Temporary list to store points for the current rupture

    with open(file, "r") as file:
        for line in file:
            line = line.strip()
            if line.startswith("#Origin") or line.startswith("#Source"):
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

def parse_eventxml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    # Get the attributes from the <earthquake> tag
    lat = float(root.attrib['lat'])
    lon = float(root.attrib['lon'])
    depth = float(root.attrib['depth'])
    return lat, lon, depth

ruptures = parse_ruptquads(f"{file_path}/rupt_quads.txt")

rupture_polygons = []

for index, row in ruptures.iterrows():
    coords = [
        (row["p1_lon"], row["p1_lat"]),
        (row["p2_lon"], row["p2_lat"]),
        (row["p3_lon"], row["p3_lat"]),
        (row["p4_lon"], row["p4_lat"]),
        (row["p1_lon"], row["p1_lat"])  # close polygon
    ]

    rupture_polygons.append({
        "geometry": Polygon(coords),
        "rupture_id": index,
        "layer": "rupture_plane",
        "color": "#00008b",   # darkblue
        "weight": 4,
        "opacity": 0.1        # transparency=90 → opacity ≈ 0.1
    })

updip_lines = []

for index, row in ruptures.iterrows():
    coords = [
        (row["p1_lon"], row["p1_lat"]),
        (row["p2_lon"], row["p2_lat"])
    ]

    updip_lines.append({
        "geometry": LineString(coords),
        "rupture_id": index,
        "layer": "updip_edge",
        "color": "#8b0000",   # darkred
        "weight": 4,
        "opacity": 0.2        # transparency=80 → opacity ≈ 0.2
    })

gdf_polygons = gpd.GeoDataFrame(    
    rupture_polygons,
    crs="EPSG:4326"
)

gdf_lines = gpd.GeoDataFrame(
    updip_lines,
    crs="EPSG:4326"
)


gdf_polygons.to_file(f"{file_path}/fault_ruptures.geojson", driver="GeoJSON")
gdf_lines.to_file(f"{file_path}/fault_updip_edges.geojson", driver="GeoJSON")


## Produce Epicenter point GeoJSON
if args.eventxml is not None:
    lat, lon, depth = parse_eventxml(args.eventxml)
    gdf_epicenter = gpd.GeoDataFrame(
        [{
            "geometry": Point(lon, lat),
            "depth": depth,
            "layer": "epicenter",
            "color": "#ff0000",   # red
            "weight": 6,
            "opacity": 1.0
        }],
        crs="EPSG:4326"
    )
    gdf_epicenter.to_file(f"{file_path}/epicenter.geojson", driver="GeoJSON")    # @todo: writes to the event-level directory instead of the current/products directory. 

# ## Produce QGIS style files
# from qgis.core import (
#     QgsVectorLayer,
#     QgsFillSymbol,
#     QgsProperty,
#     QgsSingleSymbolRenderer,
#     QgsUnitTypes
# )

# layer = QgsVectorLayer(
#     "fault_ruptures.geojson",
#     "fault_ruptures",
#     "ogr"
# )

# if not layer.isValid():
#     raise RuntimeError("Failed to load rupture layer")

# symbol = QgsFillSymbol.createSimple({})

# # Outline color & width
# symbol.symbolLayer(0).setDataDefinedProperty(
#     QgsFillSymbol.PropertyStrokeColor,
#     QgsProperty.fromField("color")
# )

# symbol.symbolLayer(0).setDataDefinedProperty(
#     QgsFillSymbol.PropertyStrokeWidth,
#     QgsProperty.fromField("weight")
# )

# symbol.symbolLayer(0).setStrokeWidthUnit(QgsUnitTypes.RenderMillimeters)

# # Fill opacity
# symbol.symbolLayer(0).setDataDefinedProperty(
#     QgsFillSymbol.PropertyFillOpacity,
#     QgsProperty.fromField("opacity")
# )

# renderer = QgsSingleSymbolRenderer(symbol)
# layer.setRenderer(renderer)

# layer.saveNamedStyle("fault_ruptures.qml")
