#!/usr/bin/env python

# Check if rupture file is a MultiPolygon 
# If not, go get the FFM FSP file and convert to rupture.json

import json
import sys
from pathlib import Path


def get_geometry_type(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    features = data.get("features", [])
    if not features:
        raise ValueError("No features found in JSON")

    # Assuming one feature (ShakeMap-style)
    geometry_type = features[0]["geometry"]["type"]
    return geometry_type


def main():
    if len(sys.argv) != 2:
        print("Usage: python check_geometry.py <file.json>")
        sys.exit(1)

    json_file = Path(sys.argv[1])
    geom_type = get_geometry_type(json_file)

    print(f"{geom_type}")

    if geom_type != "MultiPolygon":
        print("Geometry is not MultiPolygon. Need to get FSP file and convert to rupture.json.")
        # Here you would add code to fetch the FSP file and convert it to rupture.json
        # This is a placeholder for that logic
        # For example:
        # fsp_file = fetch_fsp_file(event_id)
        # convert_fsp_to_rupture(fsp_file, output_path)

if __name__ == "__main__":
    main()