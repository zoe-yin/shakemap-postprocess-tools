#!/usr/bin/env python

import sys
import argparse

###
# To test or run as a standalone script in a products directory, try using the following command:
# cd /Users/hyin/shakemap_profiles/default/data/us6000jlqa
# python /Users/hyin/soft/shakemap-postprocess-tools/calc-region_rupt_quads.py --rq1 ./np1/products/rupt_quads.txt --rq2 ./np2/products/rupt_quads.txt


# Parse command line arguments
parser = argparse.ArgumentParser(description="Parse rupt_quads.txt file and plot fault planes.")
parser.add_argument('--rq1', type=str, required=True, help='Path to the first rupt_quads.txt file')
parser.add_argument('--rq2', type=str, required=True, help='Path to the second rupt_quads.txt file')
args = parser.parse_args()

## Import functions from custom_utils.py
sys.path.append("/Users/hyin/soft/shakemap-postprocess-tools/shakemap_utils")
from custom_utils import parse_ruptquads, haversine, parse_ruptjson, parse_eventxml

rupt_np1 = parse_ruptquads(args.rq1)
rupt_np2 = parse_ruptquads(args.rq2)

def get_region_from_rq(rupture):
    min_lon = min(rupture["p1_lon"].min(), rupture["p2_lon"].min(), rupture["p3_lon"].min(), rupture["p4_lon"].min())
    max_lon = max(rupture["p1_lon"].max(), rupture["p2_lon"].max(), rupture["p3_lon"].max(), rupture["p4_lon"].max())
    min_lat = min(rupture["p1_lat"].min(), rupture["p2_lat"].min(), rupture["p3_lat"].min(), rupture["p4_lat"].min())
    max_lat = max(rupture["p1_lat"].max(), rupture["p2_lat"].max(), rupture["p3_lat"].max(), rupture["p4_lat"].max())
    # lat_buffer = (max_lat - min_lat) * 0.2  # Add 20% buffer to latitude range
    # lon_buffer = (max_lon - min_lon) * 0.2  # Add 20% buffer to longitude range
    # rgn = [min_lon-lon_buffer, max_lon+lon_buffer, min_lat-lat_buffer, max_lat+lat_buffer]  # Add returned region with buffer
    rgn = [min_lon, max_lon, min_lat, max_lat]
    return rgn

rgn1 = get_region_from_rq(rupt_np1)
rgn2 = get_region_from_rq(rupt_np2)

# Combine regions
min_lon = min(rgn1[0], rgn2[0])
max_lon = max(rgn1[1], rgn2[1])
min_lat = min(rgn1[2], rgn2[2])
max_lat = max(rgn1[3], rgn2[3]) 

lat_buffer = (max_lat - min_lat) * 0.2  # Add 20% buffer to latitude range
lon_buffer = (max_lon - min_lon) * 0.2  # Add 20% buffer to longitude range

# Final combined region
combined_rgn = [min_lon-lon_buffer, max_lon+lon_buffer, min_lat-lat_buffer, max_lat+lat_buffer]

combined_rgn_str = f"{combined_rgn[0]}/{combined_rgn[1]}/{combined_rgn[2]}/{combined_rgn[3]}"

print(
    f"{combined_rgn_str}"
)