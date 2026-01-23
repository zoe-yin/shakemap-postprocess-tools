#!/usr/bin/env python

import pandas as pd
import pygmt
from pygmt.params import Position
import os
import math
import numpy as np
import argparse
from shapely.geometry import Point, LineString
from pathlib import Path
import xml.etree.ElementTree as ET

import sys
## Import functions from custom_utils.py
sys.path.append("/Users/hyin/soft/shakemap-postprocess-tools/shakemap_utils")
from custom_utils import parse_ruptquads, haversine, parse_ruptjson, parse_eventxml, parse_im_json

###
# To test or run as a standalone script in a products directory, try using the following command:
# python /Users/hyin/soft/shakemap-postprocess-tools/plot_ruptquads/plot_ruptquads.py --file_path . --eventxml ../event.xml --cmt '/Users/hyin/shakemap_profiles/default/data/us6000rsy1/us6000rsy1_tensor.json' --np 1

# Parse command line arguments
parser = argparse.ArgumentParser(description="Parse rupt_quads.txt file and plot fault planes.")
parser.add_argument('--file_path', type=str, required=True, help='Path to the shakemap event directory')
parser.add_argument('--region', type=str, default='None', help='Region in the format xmin/xmax/ymin/ymax')
parser.add_argument('--eventxml', type=str, default=None, help='Path to the rupture event.xml file (optional). Will assume the file is one level up from the file_path if none is provided.')
parser.add_argument('--faultgeometry', type=str, default=None, help='Path to a rupture.json fault geometry file (optional).')
parser.add_argument('--cmt', type=str, default=None, help='Moment Tensor solution file saved as a json (e.g. us6000rsy1_event.json). If provided, will plot the beachball on the map.')
parser.add_argument(
    '--np',
    type=int,
    choices=[1, 2],
    default=None,
    help='Specify which nodal plane to highlight (1 or 2). Only relevant if --cmt is provided.'
)

args = parser.parse_args()


# Validate: --np only makes sense if --cmt is provided
if args.np is not None and args.cmt is None:
    parser.error("--np requires --cmt to be specified")


file_path = args.file_path
file = os.path.join(file_path, 'rupt_quads.txt')


def plot_cmt(cmt): 
    import matplotlib.pyplot as plt
    from obspy.imaging.beachball import beach
    import numpy as np

    # s1 = float(cmt['properties']['nodal-plane-1-strike'])
    # d1 = float(cmt['properties']['nodal-plane-1-dip'])
    # r1 = float(cmt['properties']['nodal-plane-1-rake'])

    mrr1 = float(cmt['properties']['tensor-mrr'])
    mtt1 = float(cmt['properties']['tensor-mtt'])
    mpp1 = float(cmt['properties']['tensor-mpp'])
    mrt1 = float(cmt['properties']['tensor-mrt'])
    mrp1 = float(cmt['properties']['tensor-mrp'])
    mtp1 = float(cmt['properties']['tensor-mtp'])

    # Moment tensor
    mt = [
        mrr1,
        mtt1,
        mpp1,
        mrt1,
        mrp1,
        mtp1,
    ]

    # Create figure and axes explicitly
    fig, ax = plt.subplots(figsize=(4, 4))

    # Create beachball (returns a PatchCollection)
    width = 200
    bb = beach(
        mt,
        xy=(0, 0),
        width=width,
        facecolor="black",
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

    eventid = cmt["properties"]["eventsourcecode"]

    plt.savefig(
        f'{file_path}/moment-tensor.png',
        dpi=300,
        bbox_inches="tight",
        pad_inches=0,
        transparent=True
    )

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
    lat_buffer = (max_lat - min_lat) * 0.2  # Add 20% buffer to latitude range
    lon_buffer = (max_lon - min_lon) * 0.2  # Add 20% buffer to longitude range
    rgn = [min_lon-lon_buffer, max_lon+lon_buffer, min_lat-lat_buffer, max_lat+lat_buffer]  # Add some padding to the region
    print(f"Determined region: {rgn}")

else: 
    rgn = args.region.split('/')
    print(f"Using provided region: {rgn}")
    rgn = [float(coord) for coord in rgn]  # Convert to float

### Read in CMT if provided
if args.cmt is not None: 
    cmtfile = args.cmt
    print(f"CMT solution provided: {cmtfile}")

    import json
    with open(cmtfile, 'r') as json_file:
        cmt = json.load(json_file)

    plot_cmt(cmt)




###################################################
############# PLOT THE FAULT RUPTURES #############
###################################################

# Initialize figure
fig = pygmt.Figure()
# Set PyGMT universal configurations
pygmt.config(FORMAT_GEO_MAP="ddd.x", MAP_FRAME_TYPE="plain", FONT="20p")
projection = 'M0/0/30c'

fig.basemap(region=rgn, projection=projection, frame=True)
fig.coast(shorelines=False, region=rgn, projection=projection, water='204/212/219')

# Plot Topo
topo = '/Users/hyin/usgs_mendenhall/topo/global_srtm15p/SRTM15_V2.7.nc' #@todo: Figure out the best way to un-hard code this
fig.grdimage(
    grid=topo,
    cmap="gray",
    shading=True,
    transparency=70,
)

## Plot PSHA
psha='/Users/hyin/usgs_mendenhall/ffsimmer/map-layers/psha/GEM-GSHM_PGA-475y-rock_v2023/v2023_1_pga_475_rock_3min.tif'
# create CPT with values less than 0.1 set to transparent
pygmt.makecpt(
    cmap="bilbao",
    series=[0.1, 1.0, 0.01],  # min, max, increment
    background="255/255/255/0",
    reverse=True
)
fig.grdimage(
    grid=psha,
    cmap=True,
    shading=True,
    transparency=40,
)
fig.colorbar(frame='af+lSeismic Hazard PGA (g) 475 yr. (GEM)', position=Position("BL", cstype="outside", offset=(-11.5, 0.5)),length=5,width=0.5, orientation='horizontal')  # forces horizontal

# Plot GEM faults
faults_global = "/Users/hyin/usgs_mendenhall/ffsimmer/map-layers/faults/gem-global-active-faults-master/gmt/gem_active_faults_harmonized.gmt"
fig.plot(
    data=faults_global,
    pen="3p,black",
    transparency=60,
    label="GEM Active Faults",
)

## Plot QFaults
qfaults = "/Users/hyin/usgs_mendenhall/ffsimmer/map-layers/faults/Qfaults_GIS/SHP/Qfaults_US_Database.gmt"
fig.plot(
    data=qfaults,
    pen="1p,orange",
    label="QFaults",
)

# # EFSM geojson not plotting for some reason
# # Plot EFSM 20 
# efsm20 = '/Users/hyin/usgs_mendenhall/ffsimmer/map-layers/faults/efsm_2020_europe-faults/EFSM20_GeoJSON/EFSM20_efsm20_cf_top.geojson'
# fig.plot(
#     data=efsm20,
#     pen="1p,purple",
#     label="EFSM20",
# )

# Plot Slab2.0
slab2 = '/Users/hyin/usgs_mendenhall/ffsimmer/map-layers/faults/slab2.0/slab2.gmt'
fig.plot(
    data=slab2,
    pen="1p,blue",
    label="Slab 2.0",
)

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

## Plot MMI contours if available
contfile = os.path.join(file_path,'cont_mmi.json')
if os.path.exists(contfile):
    gdf = parse_im_json(contfile)
    pygmt.makecpt(cmap="/Users/hyin/usgs_mendenhall/ffsimmer/styles-cpts/mmi_discrete_20bins.cpt")
    # Plot each contour with its value
    for i in range(len(gdf)):
        mi = gdf.iloc[i].value  # Extract the value for the contour
        # Only plot MMI integer contours
        if mi % 1.0 == 0:
            fig.plot(data=gdf.iloc[[i]], cmap=True, zvalue=mi, pen="3p,+z", region=rgn, projection=projection) #Plot each contour individually with its value
        elif mi % 0.5 == 0:
            fig.plot(data=gdf.iloc[[i]], cmap=True, zvalue=mi, pen="1p,+z", region=rgn, projection=projection) #Plot each contour individually with its value
        else:
            print("Something went wrong with the contours...")
    fig.colorbar(frame='af+lMMI', position=Position("BL", cstype="outside", offset=(-5.5,0.5)),length=5,width=0.5, orientation='horizontal')  # forces horizontal
    # frame='af+lSeismic Hazard PGA (g) 475 yr. (GEM)'


## Plot some stats about the ruptures
fig.text(position="BR", offset="-2c/5c", text="Avg. Aspect Ratio: " + str(round(avg_aspect,2)) ,font="20p,Helvetica,black")
fig.text(position="BR", offset="-2c/4c", text=f"Avg. Fault length: {avg_fault_length:.2f} km" ,font="20p,Helvetica,black")
fig.text(position="BR", offset="-2c/3c", text=f"Avg. updip depth: {avg_updip_depth:.2f} km" ,font="20p,Helvetica,black")
fig.text(position="BR", offset="-2c/2c", text=f"Avg. downdip depth: {avg_downdip_depth:.2f} km" ,font="20p,Helvetica,black")

## Plot the CMT solution and the nodal plane if provided
if args.cmt is not None:
    print("Plotting CMT beachball on the map.")
    
    # Plot the Obspy beachball PNG on the PyGMT figure 
    # PyGMT version 0.16.X does not allow position arguments like "TL", so I've updated to PyGMT 0.18.X
    fig.image(
        imagefile=f"{file_path}/moment-tensor.png",
        position=Position("TL",offset="1c,1c"),
        # position="TL",
        width="3c",
    )
    if args.np is not None:
        strike = cmt["properties"][f"nodal-plane-{args.np}-strike"]
        dip = cmt["properties"][f"nodal-plane-{args.np}-dip"]
        rake = cmt["properties"][f"nodal-plane-{args.np}-rake"]
        fig.text(position="TL", offset='5c/-1.2c', text=f"Nodal Plane {args.np}", font="20p,Helvetica,black")
        fig.text(position="TL", offset='5c/-2.2c', text=f"Strike: {strike}\N{DEGREE SIGN}", font="20p,Helvetica,black")
        fig.text(position="TL", offset='5c/-3.2c', text=f"Dip: {dip}\N{DEGREE SIGN}", font="20p,Helvetica,black")

fig.legend()


fig.savefig(file_path+'/ruptures_map-view.png')
