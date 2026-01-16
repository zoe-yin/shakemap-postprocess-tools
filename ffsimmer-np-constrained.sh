#!/usr/bin/env bash

# Check that an argument was provided
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 EVENTID"
    exit 1
fi

eventid="$1"
eventpath='/Users/hyin/shakemap_profiles/default/data/'${eventid}

# Check if the directory for the event already exists
if [[ -d "$eventpath/current" ]]; then
    echo "Directory ${eventpath}/current already exists. Deleting current directory."
    rm -r ${eventpath}/current
fi

sm_create "$eventid"

cd $eventpath

softpath='/Users/hyin/soft/shakemap-postprocess-tools/'

# Run getmoment.py to create the CMT file
${softpath}getmoment.py $eventid $eventpath

# Make a directory for each nodal plane
# These commands will overwrite any existing files in np1 and np2 and subsequent shake command will delete old products completely
mkdir np1 np2
cp -r current/event.xml current/dyfi_dat.json current/instrumented_dat.json np1
cp -r current/event.xml current/dyfi_dat.json current/instrumented_dat.json np2

# Get CMT variables
NP1_STRIKE=$(jq -r '.properties["nodal-plane-1-strike"]' ${eventid}_tensor.json)
NP1_DIP=$(jq -r '.properties["nodal-plane-1-dip"]' ${eventid}_tensor.json)
NP2_STRIKE=$(jq -r '.properties["nodal-plane-2-strike"]' ${eventid}_tensor.json)
NP2_DIP=$(jq -r '.properties["nodal-plane-2-dip"]' ${eventid}_tensor.json)

# Create model.conf file, set the number of simulations
FFSIM_NSIM=5
FFSIM_TRUE_GRID=True

# Create a file for the first nodal plane
OUTFILE1="np1/model.conf"

cat > "${OUTFILE1}" <<EOF
[modeling]
    ffsim_nsim = ${FFSIM_NSIM}
    ffsim_true_grid = ${FFSIM_TRUE_GRID}
    ffsim_min_strike = ${NP1_STRIKE}
    ffsim_max_strike = ${NP1_STRIKE}
    ffsim_min_dip = ${NP1_DIP}
    ffsim_max_dip = ${NP1_DIP}
EOF
echo "Wrote ${OUTFILE1}"

OUTFILE2="np2/model.conf"
cat > "${OUTFILE2}" <<EOF
[modeling]
    ffsim_nsim = ${FFSIM_NSIM}
    ffsim_true_grid = ${FFSIM_TRUE_GRID}
    ffsim_min_strike = ${NP2_STRIKE}
    ffsim_max_strike = ${NP2_STRIKE}
    ffsim_min_dip = ${NP2_DIP}
    ffsim_max_dip = ${NP2_DIP}
EOF
echo "Wrote ${OUTFILE2}"

mv current current_save

## Create ShakeMap for Nodal Plane #1
echo "Running ShakeMap for NP1 with strike=${NP1_STRIKE} and dip=${NP1_DIP}"
ln -s np1 current
shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& current/log.txt

mv current/rupt_quads.txt current/products/
cp current/model.conf current/products/
mv current/log.txt current/products/log.txt

# Plot the FFSIMMER rupture planes for NP1
echo "Plotting FFSIMMER results for NP1"
python ${softpath}plot_ruptquads/plot_ruptquads.py --file_path ${eventpath}/np1/products --cmt ${eventpath}/${eventid}_tensor.json --np 1
python ${softpath}qgis-utils/ffsimmer2qgis.py --productdir ${eventpath}/np1/products --eventxml ${eventpath}/current/event.xml
cp /Users/hyin/usgs_mendenhall/ffsimmer/styles-cpts/qgis-qmls/*.qml  ${eventpath}/np1/products/

## Create ShakeMap for Nodal Plane #2
echo "Running ShakeMap for NP2 with strike=${NP2_STRIKE} and dip=${NP2_DIP}"
rm current
ln -s np2 current
shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& current/log.txt

mv current/rupt_quads.txt current/products/
cp current/model.conf current/products/
mv current/log.txt current/products/log.txt

# Plot the FFSIMMER rupture planes for NP2
echo "Plotting FFSIMMER results for NP2"
python ${softpath}plot_ruptquads/plot_ruptquads.py --file_path ${eventpath}/np2/products --cmt ${eventpath}/${eventid}_tensor.json --np 2
python ${softpath}qgis-utils/ffsimmer2qgis.py --productdir ${eventpath}/np2/products --eventxml ${eventpath}/current/event.xml
cp /Users/hyin/usgs_mendenhall/ffsimmer/styles-cpts/qgis-qmls/*.qml  ${eventpath}/np2/products/