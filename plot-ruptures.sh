#!/bin/bash

# eventid='us6000f65h'

# Check that an argument was provided
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 EVENTID"
    exit 1
fi

eventid="$1"
softpath='/Users/hyin/soft/shakemap-postprocess-tools/'
eventpath="/Users/hyin/shakemap_profiles/default/data/${eventid}/"

# Read region from region.txt file
if [[ -f ${eventpath}"region.txt" ]]; then
    REGION=$(cat ${eventpath}region.txt)
    echo "Read region from region.txt: ${REGION}"
else
    echo "region.txt file not found."
fi

###
echo "Plotting NP1"
### 

python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/np1/products \
  --cmt ${eventpath}/${eventid}_tensor.json \
  --np 1 \
  --region="${REGION}" \
  --topo True \
  --contours True
mv ${eventpath}/np1/products/ruptures_map-view.png ${eventpath}/np1/products/ruptures_contours.png

python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/np1/products \
  --cmt ${eventpath}/${eventid}_tensor.json \
  --np 1 \
  --region="${REGION}" \
  --psha True \
  --topo True


###
echo "Plotting NP2"
### 

python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/np2/products \
  --cmt ${eventpath}/${eventid}_tensor.json \
  --np 2 \
  --region="${REGION}" \
  --topo True \
  --contours True
mv ${eventpath}/np2/products/ruptures_map-view.png ${eventpath}/np2/products/ruptures_contours.png

python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/np2/products \
  --cmt ${eventpath}/${eventid}_tensor.json \
  --np 2 \
  --region="${REGION}" \
  --psha True \
  --topo True

###
echo "Plotting current ShakeMap Reproduction"
### 

python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/shakemap_reproduction/products \
  --faultgeometry ${eventpath}/shakemap_reproduction/rupture.json \
  --region="${REGION}" \
  --contours True \
  --topo True