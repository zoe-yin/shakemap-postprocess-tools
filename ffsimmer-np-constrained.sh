#!/usr/bin/env bash

# Check that an argument was provided
if [[ $# -lt 1 ]]; then
    echo "Usage: $0 EVENTID"
    exit 1
fi

eventid="$1"
eventpath='/Users/hyin/shakemap_profiles/default/data/'${eventid}
softpath='/Users/hyin/soft/shakemap-postprocess-tools/'

cd $eventpath

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
    mv ${eventpath}/current ${eventpath}/sm_create_input
fi

## Check if the shakemap_reproduction directory is complete
if [[ -f "$eventpath/shakemap_reproduction/products/grid.xml" ]]; then
    echo "shakemap_reproduction is complete. Skipping."
else
    echo "Running shakemap_reproduction"
    if [[ -d "shakemap_reproduction" ]]; then
        echo "Directory shakemap_reproduction already exists. Deleting shakemap_reproduction directory."
        rm -r shakemap_reproduction
    fi
    # Copy sm_create files over to the reproduction directory
    cp -r ${eventpath}/sm_create_input ${eventpath}/shakemap_reproduction
    ln -s ${eventpath}/shakemap_reproduction ${eventpath}/current

    # Check if alternate rupture file exists
    if [[ -f "$eventpath/shakemap_fault.txt" ]]; then
        echo "Using alternate ShakeMap Polygon File (shakemap_fault.txt)"
        rm ${eventpath}/shakemap_reproduction/rupture.json
        cp ${eventpath}/shakemap_fault.txt ${eventpath}/shakemap_reproduction/
        echo "Running the current ShakeMap..."
        shake $eventid assemble -c "rupture config" model rupture contour mapping info gridxml raster >& ${eventpath}/current/log.txt
        cp ${eventpath}/shakemap_reproduction/products/rupture.json ${eventpath}/shakemap_reproduction/rupture.json
        rm -r ${eventpath}/current
    else
        echo "Running the current ShakeMap..."
        shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& ${eventpath}/current/log.txt
        mv ${eventpath}/current/rupt_quads.txt ${eventpath}/current/products/
        rm -r $eventpath/current
    fi
fi

# ## Extract the tectonic setting from strec_results.json
# json_file=${eventpath}'/shakemap_reproduction/strec_results.json'
# echo $json_file
# TectonicRegion=$(python3 -c "import json; print(json.load(open('$json_file'))['TectonicRegion'])")
# FocalMechanism=$(python3 -c "import json; print(json.load(open('$json_file'))['FocalMechanism'])")
# ProbabilityActive=$(python3 -c "import json; print(json.load(open('$json_file'))['ProbabilityActive'])")
# ProbabilitySubductionCrustal=$(python3 -c "import json; print(json.load(open('$json_file'))['ProbabilitySubductionCrustal'])")
# ProbabilitySubductionInterface=$(python3 -c "import json; print(json.load(open('$json_file'))['ProbabilitySubductionInterface'])")
# ProbabilitySubductionIntraslab=$(python3 -c "import json; print(json.load(open('$json_file'))['ProbabilitySubductionIntraslab'])")

## Check if the ffsimmer_pointsource directory is complete
if [[ -f "$eventpath/ffsimmer_pointsource/products/rupt_quads.txt" ]]; then
    echo "ffsimmer_pointsource is complete. Skipping."
else
    echo "Running ffsimmer_pointsource"
    if [[ -d "$eventpath/ffsimmer_pointsource" ]]; then
        echo "Directory ffsimmer_pointsource already exists. Deleting ffsimmer_pointsource directory."
        rm -r $eventpath/ffsimmer_pointsource
    fi
    echo "Running Point Source comparison shakemap..."
    mkdir $eventpath/ffsimmer_pointsource
    cp -r $eventpath/sm_create_input/event.xml $eventpath/ffsimmer_pointsource/
    ln -s $eventpath/ffsimmer_pointsource $eventpath/current
    shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& $eventpath/current/log.txt
    mv ${eventpath}/current/rupt_quads.txt ${eventpath}/current/products/
    mv ${eventpath}/current/log.txt ${eventpath}/current/products/log.txt
    rm -r $eventpath/current
fi

## Prep NP1 and NP2 configuration files
read NP1_STRIKE NP1_DIP NP1_RAKE \
        NP2_STRIKE NP2_DIP NP2_RAKE \
        < <(python "${softpath}get-moment-tensor/getMomentTensor.py" "${eventid}" "${eventpath}" )
echo "NP1 strike, dip rake: $NP1_STRIKE $NP1_DIP $NP1_RAKE"

# Create model.conf file, set the number of simulations
FFSIM_NSIM=20
FFSIM_TRUE_GRID=True

# Create a file for the first nodal plane
OUTFILE1=${eventpath}"/np1_model.conf"
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

# Create a file for the second nodal plane
OUTFILE2=${eventpath}"/np2_model.conf"
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

## Check if NP1 and NP2 directories are complete
required_files=(
    "$eventpath/np1/products/rupt_quads.txt"
    "$eventpath/np2/products/rupt_quads.txt"
)

missing=false
for f in "${required_files[@]}"; do
    [[ -f "$f" ]] || { missing=true; break; }
done

# if ! $missing; then
if [[ $missing == false ]]; then
    echo "NP1 and NP2 directories are complete. Skipping."
else
    echo "Running NP1 and NP2 shakemaps"
    ## Clear and Set Up the NP1 and NP2 directories
    if [[ -d "$eventpath/np1" ]]; then
        echo "Directory np1 already exists. Deleting np1 directory."
        rm -r $eventpath/np1
    fi
    if [[ -d "$eventpath/np2" ]]; then
        echo "Directory np2 already exists. Deleting np2 directory."
        rm -r $eventpath/np2
    fi
    mkdir $eventpath/np1 $eventpath/np2
    mv $eventpath/np1_model.conf $eventpath/np1/model.conf
    cp -r $eventpath/sm_create_input/event.xml $eventpath/np1
    mv $eventpath/np2_model.conf $eventpath/np2/model.conf
    cp -r $eventpath/sm_create_input/event.xml $eventpath/np2

    # Run ShakeMap for NP1
    ln -s $eventpath/np1 $eventpath/current
    shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& $eventpath/current/log.txt
    mv $eventpath/current/rupt_quads.txt $eventpath/current/products/
    cp $eventpath/current/model.conf $eventpath/current/products/
    mv $eventpath/current/log.txt $eventpath/current/products/log.txt
    rm $eventpath/current

    # Run ShakeMap for NP2
    ln -s $eventpath/np2 $eventpath/current
    shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& $eventpath/current/log.txt
    mv $eventpath/current/rupt_quads.txt $eventpath/current/products/
    cp $eventpath/current/model.conf $eventpath/current/products/
    mv $eventpath/current/log.txt $eventpath/current/products/log.txt
    rm $eventpath/current
fi

## Get region dimensions from both rupt_quad.txt files
REGION=$(python /Users/hyin/soft/shakemap-postprocess-tools/calc-region_rupt_quads.py --rq1 ${eventpath}/np1/products/rupt_quads.txt --rq2 ${eventpath}/np2/products/rupt_quads.txt)
echo "Using region: ${REGION}"

# write the region to a file for later use
echo "${REGION}" > ${eventpath}/region.txt
