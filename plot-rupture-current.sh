#!/usr/bin/env bash

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
echo "Plotting current directory"
### 

python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/current/products \
  --region="${REGION}" \
  --topo True \
  --contours True \
  --ruptquads True
mv ${eventpath}/current/products/ruptures_map-view.png ${eventpath}/current/products/ruptures_contours.png

python ${softpath}plot_ruptquads/plot_ruptquads.py \
  --file_path ${eventpath}/current/products \
  --ruptquads True \
  --region="${REGION}" \
  --topo True \
  --ruptquads True

