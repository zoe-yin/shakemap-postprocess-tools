#!/usr/bin/env python

import sys
import argparse

###
# To test or run as a standalone script in a products directory, try using the following command:
# cd /Users/hyin/shakemap_profiles/default/data/us6000jlqa
# python /Users/hyin/soft/shakemap-postprocess-tools/calc-region_rupt_quads.py --rq1 ./np1/products/rupt_quads.txt --rq2 ./np2/products/rupt_quads.txt


# # Parse command line arguments
# parser = argparse.ArgumentParser(description="Parse rupt_quads.txt file and plot fault planes.")
# parser.add_argument('--rq1', type=str, required=True, help='Path to the first rupt_quads.txt file')
# parser.add_argument('--rq2', type=str, required=True, help='Path to the second rupt_quads.txt file')
# args = parser.parse_args()

parser = argparse.ArgumentParser(
    description="Compute combined region from one or more rupt_quads.txt files." \
    "Example usage: python calc-region_rupt_quads.py \
    --rq file1.txt file2.txt file3.txt file4.txt" \
)

parser.add_argument(
    "--rq",
    nargs="+",              # Can take one or more file paths
    required=True,
    help="Paths to rupt_quads.txt files (space-separated)"
)

parser.add_argument(
    "--buffer",
    type=float,
    default=0.8,
    help="Fractional buffer to apply (default: 0.8)"
)

args = parser.parse_args()

## Import functions from custom_utils.py
sys.path.append("/Users/hyin/soft/shakemap-postprocess-tools/shakemap_utils")
from custom_utils import parse_ruptquads, haversine, parse_ruptjson, parse_eventxml

def get_region_from_rq(rupture):
    min_lon = min(rupture["p1_lon"].min(), rupture["p2_lon"].min(), rupture["p3_lon"].min(), rupture["p4_lon"].min())
    max_lon = max(rupture["p1_lon"].max(), rupture["p2_lon"].max(), rupture["p3_lon"].max(), rupture["p4_lon"].max())
    min_lat = min(rupture["p1_lat"].min(), rupture["p2_lat"].min(), rupture["p3_lat"].min(), rupture["p4_lat"].min())
    max_lat = max(rupture["p1_lat"].max(), rupture["p2_lat"].max(), rupture["p3_lat"].max(), rupture["p4_lat"].max())
    rgn = [min_lon, max_lon, min_lat, max_lat]
    return rgn

# rupt_np1 = parse_ruptquads(args.rq1)
# rupt_np2 = parse_ruptquads(args.rq2)
regions = []

for rq_file in args.rq:
    rupture = parse_ruptquads(rq_file)
    rgn = get_region_from_rq(rupture)
    regions.append(rgn)

# Combine regions
min_lon = min(r[0] for r in regions)
max_lon = max(r[1] for r in regions)
min_lat = min(r[2] for r in regions)
max_lat = max(r[3] for r in regions)

lat_buffer = (max_lat - min_lat) * args.buffer
lon_buffer = (max_lon - min_lon) * args.buffer

combined_rgn = [
    min_lon - lon_buffer,
    max_lon + lon_buffer,
    min_lat - lat_buffer,
    max_lat + lat_buffer,
]
combined_rgn_str = (
    f"{combined_rgn[0]}/{combined_rgn[1]}/"
    f"{combined_rgn[2]}/{combined_rgn[3]}"
)

print(combined_rgn_str)