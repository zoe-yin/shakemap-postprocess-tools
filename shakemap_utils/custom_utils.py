import pandas as pd
import pygmt
import os
import math
import numpy as np
import argparse
from shapely.geometry import Point, LineString
from pathlib import Path
import xml.etree.ElementTree as ET
import json

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

def get_geometry_type(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    features = data.get("features", [])
    if not features:
        raise ValueError("No features found in JSON")

    # Assuming one feature (ShakeMap-style)
    geometry_type = features[0]["geometry"]["type"]
    return geometry_type

def dims_from_ruptjson(file):
    """
    Parse a JSON file containing rupture data and calculate the length and width of the rupture.
    Args:
        file: Path to the JSON file.
    Returns:
        length and width of the rupture in meters. 
    """
    import geopandas as gpd
    import pandas as pd
    import numpy as np
    from shapely.ops import transform
    # json_path = '/Users/hyin/shakemap_profiles/default/data/us6000f65h/shakemap_reproduction/rupture.json'      # single segment
    # json_path = '/Users/hyin/shakemap_profiles/default/data/us6000jllz/shakemap_reproduction/rupture.json'    # multi-segment along-strike (Türkiye)
    # json_path = '/Users/hyin/shakemap_profiles/default/data/us6000qw60/shakemap_reproduction/rupture.json'      # multi-segment along-dip (Kamchatka)
    # json_path = '/Users/hyin/shakemap_profiles/default/data/official20041226005853450_30/rupture.json'    # 2004 Sumatra (multi-segment along-dip)

    # Check if the geometry type is a point, MultiPolygon or something else?
    type = get_geometry_type(file)
    if type == 'Point': 
        print (f"Geometry type: {type}, SKIPPING")
        length=float('nan')
        width=float('nan')
    else: 
        gdf = gpd.read_file(file)
        # Estimate appropriate UTM CRS
        utm_crs = gdf.estimate_utm_crs()

        # Reproject to meters (this drops Z, so we'll reattach it manually later)
        gdf_utm = gdf.to_crs(utm_crs)
        def scale_z(x, y, z=None):
            if z is None:
                return (x, y)
            return (x, y, z * 1000.0)

        # Convert the Z coordinate from km to m
        gdf_utm["geometry"] = gdf_utm["geometry"].apply(
            lambda geom: transform(scale_z, geom)
        )

        geom = gdf_utm.geometry.iloc[0]

        dip_segment_id = 0
        along_dip_counts = 0   # number of rings per polygon
        top_edges = []          # for detecting along-strike segmentation
        rows = []

        for poly in geom.geoms:
            # collect all rings (exterior + interiors)
            # For ShakeMap rupture.json files, each ring corresponds to a unique segment, 
            # but can be either along-strike segements (usually representing a discontinuous fault) or along-dip (usually representing a subduction interface)
            # each ring can contain a complex geometry with many top-edge vertices, so we calculate along-strike length 
            rings = [poly.exterior] + list(poly.interiors)
            print(f"Number of rings {len(rings)}")
            
            total_length = 0
            total_width = 0
            for ring in rings:
                coords = list(ring.coords)  # pull coordinates for each ring
                along_strike_segments = (((len(coords) -1)/2)) -1
                print(f"Along-strike segments {int(along_strike_segments)}")
                # Calc along-dip length
                dip_length = 0
                # Find the two points that deliniate along-dip vector
                dip_length += np.linalg.norm(np.array(coords[0]) - np.array(coords[-2]))
                # Calc along-strike length
                strike_length = 0
                for i in range(int(along_strike_segments)): 
                    strike_length += np.linalg.norm(np.array(coords[i+1]) - np.array(coords[i]))
                for j, (x, y, z) in enumerate(coords):
                    rows.append({
                        "dip_segment_id": dip_segment_id,
                        "vertex_id": j,
                        "x": x,
                        "y": y,
                        "z": z,
                        "strike_length": strike_length,
                        "dip_length": dip_length
                    })
                print(f"Segement length along-strike (m): {strike_length}")
                print(f"Segement width along-dip (m): {dip_length}")
                print(dip_length)

                dip_segment_id += 1
                total_length += strike_length
                total_width += dip_length

        df = pd.DataFrame(rows)
        # Check the number of unique depth values
        dip_segments = df['z'].nunique() - 1

        for i in range(len(rings)): 
            if dip_segments > 1:
                width = total_width
                length = total_length / dip_segments
            elif along_strike_segments > 1: 
                length = total_length
                # Confirm only 1 along-dip segment
                if dip_segments > 1: 
                    print("Error: More than 1 along-dip segment detected when calculating length for along-strike segmentation. Check the geometry and segmentation logic.")
                print(f"Along-dip segments: {dip_segments}")
                width = dip_length  # assumes that if there is >1 along-strike segment then there is only 1 along-dip segment
            else: 
                length = total_length 
                width = total_width

        print(f"Total length (m): {length}")
        print(f"Total width (m): {width}")
        print(f"Number of along-dip segments: {dip_segments}")
    return length, width


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

def parse_mt(mtfile): 
    """
    Parse a JSON file containing moment tensor information (e.g., us6000rsy1_tensor.json) and pass back a moment tensor object
    Args:
        cmtfile: Path to the MT JSON file.
        output (optional): Path to write the beachball jpeg, defaults to the location of the json file. 
    Returns:
        Moment tensor obejct (list of 6 components: mrr, mtt, mpp, mrt, mrp, mtp)
    """
    import matplotlib.pyplot as plt
    from obspy.imaging.beachball import beach
    import numpy as np
  

    # # Find some info about the event from the JSON file, e.g., eventid, time, location, etc.
    # inputdir = os.path.dirname(mtfile)
    # eventid = os.path.basename(mtfile).split("_tensor.json")[0]

    import json
    with open(mtfile, 'r') as json_file:
        mt_dict = json.load(json_file)

    # s1 = float(cmt['properties']['nodal-plane-1-strike'])
    # d1 = float(cmt['properties']['nodal-plane-1-dip'])
    # r1 = float(cmt['properties']['nodal-plane-1-rake'])

    mrr1 = float(mt_dict['properties']['tensor-mrr'])
    mtt1 = float(mt_dict['properties']['tensor-mtt'])
    mpp1 = float(mt_dict['properties']['tensor-mpp'])
    mrt1 = float(mt_dict['properties']['tensor-mrt'])
    mrp1 = float(mt_dict['properties']['tensor-mrp'])
    mtp1 = float(mt_dict['properties']['tensor-mtp'])

    eventid = mt_dict["properties"]['eventsource'] + mt_dict["properties"]["eventsourcecode"]
    # print(mt_dict["properties"])

    # write moment tensor comonents as a list
    mt = [
        mrr1,
        mtt1,
        mpp1,
        mrt1,
        mrp1,
        mtp1,
    ]

    return mt, eventid

def plot_mt(mt, eventid, outdir=None, depth=None, pager=None):
    """
    Plot a moment tensor as a beachball as a PNG that can be used in the catalog. 
    The PNG will be saved in the specified output directory (or current working directory if not specified) with the name "{eventid}_moment-tensor.png".
    Args:
        mt: Moment tensor object (list of 6 components).
        eventid: Event ID.
        outdir: Output directory for the plot (default is the current working directory)
    """
    import matplotlib.pyplot as plt
    from obspy.imaging.beachball import beach
    import numpy as np
    if outdir is None:
        outdir = os.getcwd()

    if depth is None:
        color='black' # Default color if depth if not provided
    else:
        # # Define a colormap for depth (you can customize this as needed)
        # cmap = plt.get_cmap('magma')
        # norm_depth = min(max(depth / 500, 0), 1)  # Normalize depth to [0, 1] range (assuming max depth of 200 km)
        # color = cmap(norm_depth)
        depth_min = 0
        depth_max = 200

        norm_depth = (depth - depth_min) / (depth_max - depth_min)
        norm_depth = max(0, min(norm_depth, 1))
        cmap = plt.get_cmap('magma_r')
        color = cmap(norm_depth)

    if pager is not None:
        # Define a colormap for PAGER alert level
        pager_colors = {
            'green':  '#2E8B57',
            'yellow': '#F4C430',
            'orange': '#F28C28',
            'red':    '#B22222',
        }
        color = pager_colors.get(pager.lower(), color)  # Use PAGER color if valid, otherwise use depth color

    # Create figure and axes explicitly
    fig, ax = plt.subplots(figsize=(4, 4))

    # Create beachball (returns a PatchCollection)
    width = 200
    bb = beach(
        mt,
        xy=(0, 0),
        width=width,
        facecolor=color,
        linewidth=1
    )

    # Add to axes
    ax.add_collection(bb)
    r = width / 1.9

    # Scale the figure to fit the beachball
    ax.set_xlim(-r, r)
    ax.set_ylim(-r, r)

    ax.set_aspect("equal")
    ax.axis("off")

    plt.savefig(
        f'{outdir}/{eventid}_moment-tensor.png',
        dpi=300,
        bbox_inches="tight",
        pad_inches=0,
        transparent=True
    )
    plt.close(fig)
    print(f"Saved beachball PNG to {outdir}/{eventid}_moment-tensor.png")