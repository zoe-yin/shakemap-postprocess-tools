#!/usr/bin/env bash

# Check that an argument was provided
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 EVENTID"
    exit 1
fi

eventid="$1"
eventpath='/Users/hyin/shakemap_profiles/default/data/'${eventid}
softpath='/Users/hyin/soft/shakemap-postprocess-tools/'

# Check if a "current" directory for the event already exists
if [[ -d "$eventpath/current" ]]; then
    echo "Directory ${eventpath}/current already exists. Deleting current directory."
    rm -r ${eventpath}/current
fi

## Check if sm_create has already been run and saved as sm_create_input
if [[ -f "$eventpath/sm_create_input/event.xml" ]]; then
    echo "sm_create has already been run. Skipping"
else
    echo "Running sm_create"
    sm_create "$eventid"
    mv current sm_create_input
fi

## Check if the shakemap_reproduction directory is complete
if [[ -f "$eventpath/shakemap_reproduction/products/grid.xml" ]]; then
    echo "shakemap_reproduction is complete. Skipping."
else
    echo "Running shakemap_reproduction"
    # your commands here
fi

## Check if the ffsimmer_pointsource directory is complete
if [[ -f "$eventpath/ffsimmer_pointsource/products/rupt_quads.txt" ]]; then
    echo "ffsimmer_pointsource is complete. Skipping."
else
    echo "Running ffsimmer_pointsource"
    # your commands here
fi

## Check if NP1 and NP2 are present
if [[ -f "$eventpath/np1/products/rupt_quads.txt" ]]; then
    echo "NP1 is complete. Skipping"
else
    echo "Running NP1"
    # your commands here
fi


# sm_create "$eventid"

# cd $eventpath

# echo $eventid
# echo $eventpath

# ## Check if np1 and np2 directories already exist, if so delete them
# if [[ -d "np1" ]]; then
#     echo "Directory np1 already exists. Deleting np1 directory."
#     rm -r np1
# fi

# if [[ -d "np2" ]]; then
#     echo "Directory np2 already exists. Deleting np2 directory."
#     rm -r np2
# fi

# mkdir np1 np2
# cp -r current/event.xml np1 # current/dyfi_dat.json current/instrumented_dat.json
# cp -r current/event.xml np2 # current/dyfi_dat.json current/instrumented_dat.json

# read NP1_STRIKE NP1_DIP NP1_RAKE \
#      NP2_STRIKE NP2_DIP NP2_RAKE \
#      < <(python "${softpath}get-moment-tensor/getMomentTensor.py" "${eventid}" "${eventpath}" )


# echo "NP1 strike, dip rake: $NP1_STRIKE $NP1_DIP $NP1_RAKE"

# # Create model.conf file, set the number of simulations
# FFSIM_NSIM=7
# FFSIM_TRUE_GRID=True

# # Create a file for the first nodal plane
# OUTFILE1="np1/model.conf"
# cat > "${OUTFILE1}" <<EOF
# [modeling]
#     ffsim_nsim = ${FFSIM_NSIM}
#     ffsim_true_grid = ${FFSIM_TRUE_GRID}
#     ffsim_min_strike = ${NP1_STRIKE}
#     ffsim_max_strike = ${NP1_STRIKE}
#     ffsim_min_dip = ${NP1_DIP}
#     ffsim_max_dip = ${NP1_DIP}
# EOF
# echo "Wrote ${OUTFILE1}"


# # Create a file for the second nodal plane
# OUTFILE2="np2/model.conf"
# cat > "${OUTFILE2}" <<EOF
# [modeling]
#     ffsim_nsim = ${FFSIM_NSIM}
#     ffsim_true_grid = ${FFSIM_TRUE_GRID}
#     ffsim_min_strike = ${NP2_STRIKE}
#     ffsim_max_strike = ${NP2_STRIKE}
#     ffsim_min_dip = ${NP2_DIP}
#     ffsim_max_dip = ${NP2_DIP}
# EOF
# echo "Wrote ${OUTFILE2}"

# # Check if sm_create_input directory exists, if so delete it
# if [[ -d "sm_create_input" ]]; then
#     echo "Directory sm_create_input already exists. Deleting sm_create_input directory."
#     rm -r sm_create_input
# fi
# mv current sm_create_input

# ## Create ShakeMap for Nodal Plane #1
# echo "Running ShakeMap for NP1 with strike=${NP1_STRIKE} and dip=${NP1_DIP}"
# ln -s np1 current
# shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& current/log.txt

# mv current/rupt_quads.txt current/products/
# cp current/model.conf current/products/
# mv current/log.txt current/products/log.txt

# ## Create ShakeMap for Nodal Plane #2
# echo "Running ShakeMap for NP2 with strike=${NP2_STRIKE} and dip=${NP2_DIP}"
# rm current
# ln -s np2 current
# shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& current/log.txt

# mv current/rupt_quads.txt current/products/
# cp current/model.conf current/products/
# mv current/log.txt current/products/log.txt

# ## Get region dimensions from both rupt_quad.txt files
# REGION=$(python /Users/hyin/soft/shakemap-postprocess-tools/calc-region_rupt_quads.py --rq1 ${eventpath}/np1/products/rupt_quads.txt --rq2 ${eventpath}/np2/products/rupt_quads.txt)
# echo "Using region: ${REGION}"

# # write the region to a file for later use
# echo "${REGION}" > ${eventpath}/region.txt

# # Run Point Source comparison shakemap
# rm -r current
# if [[ -d "ffsimmer_pointsource" ]]; then
#     echo "Directory ffsimmer_pointsource already exists. Deleting ffsimmer_pointsource directory."
#     rm -r ffsimmer_pointsource
# fi
# echo "Running Point Source comparison shakemap..."
# mkdir current
# cp -r sm_create_input/event.xml current/
# shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& current/log.txt
# mv current ffsimmer_pointsource

# mv ffsimmer_pointsource/rupt_quads.txt ffsimmer_pointsource/products/
# mv ffsimmer_pointsource/log.txt ffsimmer_pointsource/products/log.txt

# # Run most recent shakemap
# rm current
# echo "Running sm_create once more..."
# # sm_create "$eventid"
# cp -r sm_create_input current

# echo "Running the current ShakeMap..."
# shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& current/log.txt

# # Check if current_recent directory exists, if so delete it
# if [[ -d "shakemap_reproduction" ]]; then
#     echo "Directory shakemap_reproduction already exists. Deleting shakemap_reproduction directory."
#     rm -r shakemap_reproduction
# fi
# mv current shakemap_reproduction