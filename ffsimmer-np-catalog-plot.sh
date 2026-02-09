#!/usr/bin/env bash

# Check that an argument was provided
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 EVENTID"
    exit 1
fi

eventid="$1"
eventpath='/Users/hyin/shakemap_profiles/default/data/'${eventid}
softpath='/Users/hyin/soft/shakemap-postprocess-tools/'

np1_products="${eventpath}/np1/products"
np2_products="${eventpath}/np2/products"
shakemap_reproduction_products="${eventpath}/shakemap_reproduction/products"

if [[ -d "$np1_products" && -d "$np2_products" && -d "$shakemap_reproduction_products" ]]; then
    echo "All specified directories exist."
    # Commands to execute if all directories are found
else
    echo "One or more directories are missing."
    echo "Expected directories:"
    echo "1. ${np1_products}"
    echo "2. ${np2_products}"
    echo "3. ${shakemap_reproduction_products}"
    # Commands to execute if any directory is missing
fi

# plot ruptures for np1, np2, and shakemap reproduction
# read in region file from region.txt
REGION=$(cat ${eventpath}/region.txt)
echo "Using region: ${REGION}"


# Plot np1 rupture
python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/np1/products \
  --cmt ${eventpath}/${eventid}_tensor.json \
  --np 1 \
  --region="${REGION}" \
  --psha True \
  --topo True

# Plot NP2 rupture
python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/np2/products \
  --cmt ${eventpath}/${eventid}_tensor.json \
  --np 2 \
  --region="${REGION}" \
  --psha True \
  --topo True

echo "Plotting the current ShakeMap"
python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/shakemap_reproduction/products \
  --faultgeometry ${eventpath}/shakemap_reproduction/rupture.json \
  --region="${REGION}" \
  --contours True \
  --topo True