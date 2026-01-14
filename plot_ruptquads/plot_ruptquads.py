import pandas as pd
import pygmt
import os
import math
import numpy as np
import argparse
from shapely.geometry import Point, LineString
from pathlib import Path
import xml.etree.ElementTree as ET


# Parse command line arguments
parser = argparse.ArgumentParser(description="Parse rupt_quads.txt file and plot fault planes.")
parser.add_argument('--file_path', type=str, required=True, help='Path to the shakemap event directory')
parser.add_argument('--region', type=str, default='None', help='Region in the format xmin/xmax/ymin/ymax')
parser.add_argument('--eventxml', type=str, default=None, help='Path to the rupture event.xml file (optional). Will assume the file is one level up from the file_path if none is provided.')
parser.add_argument('--faultgeometry', type=str, default=None, help='Path to a rupture.json fault geometry file (optional).')
args = parser.parse_args()

file_path = args.file_path
file = os.path.join(file_path, 'rupt_quads.txt')

def parse_ruptquads(file):
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

def parse_eventxml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    # Get the attributes from the <earthquake> tag
    lat = float(root.attrib['lat'])
    lon = float(root.attrib['lon'])
    depth = float(root.attrib['depth'])
    return lat, lon, depth
    
###################################################
#                   CALCULATIONS                #
###################################################

ruptures = parse_ruptquads(file)

ruptures["fault_length_km"] = ruptures.apply(lambda row: haversine(row["p1_lat"], row["p1_lon"], row["p2_lat"], row["p2_lon"]), axis=1)
ruptures["fault_width_km"] = np.sqrt((ruptures.apply(lambda row: haversine(row["p1_lat"], row["p1_lon"], row["p4_lat"], row["p4_lon"]), axis=1)**2)+ (ruptures["p4_depth"]**2))
ruptures["aspect_ratio"] = ruptures["fault_length_km"] / ruptures["fault_width_km"]

# Calculate average aspect ratio
avg_aspect = ruptures["aspect_ratio"].mean()
avg_fault_length = ruptures["fault_length_km"].mean()
# Calculate average updip depth
avg_updip_depth = ruptures[["p1_depth"]].mean(axis=1).mean()
avg_downdip_depth = ruptures[["p3_depth"]].mean(axis=1).mean()
print(f"Average aspect ratio: {avg_aspect:.2f}")
print(f"Average Fault length: {avg_fault_length:.2f} km")
print(f"Average updip depth: {avg_updip_depth:.2f} km")
print(f"Average downdip depth: {avg_downdip_depth:.2f} km")

## Get hypocenter from the event.xml file
if args.eventxml is not None:
    lat, lon, depth = parse_eventxml(args.eventxml)
    print(f'lat, lon, depth = ',lat, lon, depth)
else:
    eventpath = Path(file_path).parents[0] / 'event.xml'
    lat, lon, depth = parse_eventxml(eventpath)
    print(f"Using default event XML file at: {eventpath}.")
# check if the eventpath exists
# if not os.path.exists(eventpath):
#     print(f"Event XML file not found at {eventpath}. Continue plotting without hypocenter.")
#     lat, lon, depth = None, None, None
# else: 
#     print(f"Event XML file found at {eventpath}. Proceeding with parsing.")
# print(eventpath)

hypocenter = [lon, lat]

# Check if rupture.json file is provided
ruptjson=None
if args.faultgeometry is not None:
    ruptjson = args.faultgeometry
    if not os.path.exists(ruptjson):
        print(f"Rupture JSON file not found at {ruptjson}. Continue plotting without USGS fault geometry.")
        ruptjson = None
    else:
        print(f"Rupture JSON file found at {ruptjson}. Proceeding with parsing.")

# Check if region is provided
if args.region == 'None':
    print("No region provided. Automatically determining region from rupture data.")
    min_lon = min(ruptures["p1_lon"].min(), ruptures["p2_lon"].min(), ruptures["p3_lon"].min(), ruptures["p4_lon"].min())
    max_lon = max(ruptures["p1_lon"].max(), ruptures["p2_lon"].max(), ruptures["p3_lon"].max(), ruptures["p4_lon"].max())
    min_lat = min(ruptures["p1_lat"].min(), ruptures["p2_lat"].min(), ruptures["p3_lat"].min(), ruptures["p4_lat"].min())
    max_lat = max(ruptures["p1_lat"].max(), ruptures["p2_lat"].max(), ruptures["p3_lat"].max(), ruptures["p4_lat"].max())
    rgn = [min_lon-0.5, max_lon+0.5, min_lat-0.5, max_lat+0.5]  # Add some padding to the region
    print(f"Determined region: {rgn}")

else: 
    print(f"Using provided region: {rgn}")
    rgn = args.region.split('/')
    rgn = [float(coord) for coord in rgn]  # Convert to float


###################################################
############# PLOT THE FAULT RUPTURES #############
###################################################

# Initialize figure
fig = pygmt.Figure()
# Set PyGMT universal configurations
pygmt.config(FORMAT_GEO_MAP="ddd.x", MAP_FRAME_TYPE="plain", FONT="14p")
projection = 'M0/0/30c'

fig.basemap(region=rgn, projection=projection, frame=True)
fig.coast(shorelines=False, region=rgn, projection=projection, water='204/212/219')
## Plot Fault ruptures (iterate over each fault)
for index, row in ruptures.iterrows():
    # Extract points for the fault rupture
    p1 = [row['p1_lon'],row['p1_lat']]
    p2 = [row['p2_lon'],row['p2_lat']]
    p3 = [row['p3_lon'],row['p3_lat']]
    p4 = [row['p4_lon'],row['p4_lat']]
    p5 = [row['p1_lon'], row['p1_lat']]  # Closing the polygon

    if index == 0:
        # Only add label for the first fault to avoid duplicate legend entries
        # Plot the rupture plane projected to the surface
        fig.plot(x=[p1[0], p2[0], p3[0], p4[0], p5[0]], y=[p1[1], p2[1], p3[1], p4[1],p5[1]], pen='4p,darkblue',  transparency=90, label=f"Fault Realizations +S.5c", region=rgn, projection=projection)
        # Plot the updip edge
        fig.plot(x=[p1[0], p2[0]], y=[p1[1], p2[1]], pen='4p,darkred',  transparency=80, label=f"Fault Updip edge +S.5c", region=rgn, projection=projection)
    else:
        fig.plot(x=[p1[0], p2[0], p3[0], p4[0], p5[0]], y=[p1[1], p2[1], p3[1], p4[1],p5[1]], pen='4p,darkblue',  transparency=90, region=rgn, projection=projection)
        fig.plot(x=[p1[0], p2[0]], y=[p1[1], p2[1]], pen='4p,darkred',  transparency=80, region=rgn, projection=projection)
    

# Plot hypocenter
fig.plot(x=hypocenter[0], y = hypocenter[1], style="a0.9c", fill="darkorange", label="M7.8 Hypocenter")

if ruptjson is not None:
    print("Add: plotting for fault geometry from rupture.json")
    x,y = parse_ruptjson(ruptjson)
    fig.plot(x=x, y=y, pen="2p,black", label="USGS Finite Fault Geometry")
    fig.plot(x=[x[0], x[1]], y=[y[0],y[1]], pen="2p,red", label="USGS Fault Top Edge")

## Plot some stats about the ruptures
fig.text(position="BR", offset="-2c/5c", text="Avg. Aspect Ratio: " + str(round(avg_aspect,2)) ,font="20p,Helvetica,black")
fig.text(position="BR", offset="-2c/4c", text=f"Avg. Fault length: {avg_fault_length:.2f} km" ,font="20p,Helvetica,black")
fig.text(position="BR", offset="-2c/3c", text=f"Avg. updip depth: {avg_updip_depth:.2f} km" ,font="20p,Helvetica,black")
fig.text(position="BR", offset="-2c/2c", text=f"Avg. downdip depth: {avg_downdip_depth:.2f} km" ,font="20p,Helvetica,black")

fig.legend()

fig.savefig(file_path+'/ruptures_map-view.png')
