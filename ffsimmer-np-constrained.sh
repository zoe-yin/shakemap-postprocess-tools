#!/usr/bin/env bash

#!/usr/bin/env bash

set -euo pipefail

usage() {
    echo "Usage: $0 [-u] [-c] [-r] EVENTID"
    echo "  -u : run unconstrained (ffsimmer_pointsource)"
    echo "  -c : run constrained (NP1/NP2)"
    echo "  -r : run reproduction"
    exit 1
}

# Default is to not run anything
run_unconstrained=false
run_constrained=false
run_reproduction=false

# Parse flags
while getopts ":ucr" opt; do
    case ${opt} in
        u) run_unconstrained=true ;;
        c) run_constrained=true ;;
        r) run_reproduction=true ;;
        *) usage ;;
    esac
done
shift $((OPTIND - 1))

# Require EVENTID
[[ $# -lt 1 ]] && usage
eventid="$1"

# Optional: if no flags provided, run everything
if ! $run_unconstrained && ! $run_constrained && ! $run_reproduction; then
    echo "No flags provided."
    usage
fi

# eventid="$1"
eventpath='/Users/hyin/shakemap_profiles/default/data/'${eventid}
softpath='/Users/hyin/soft/shakemap-postprocess-tools/'

## Check if the event directory exists
if [[ ! -d "$eventpath" ]]; then
    echo "Creating event directory: $eventpath"
    mkdir $eventpath
fi

cd $eventpath


# Check if a "current" directory for the event already exists
if [[ -d "$eventpath/current" ]]; then
    echo "Directory ${eventpath}/current already exists. Deleting current directory."
    rm -r ${eventpath}/current
fi

#############################################
#           Reproduction ShakeMap           #
#############################################

# Check if the user wants to run the reproduction ShakeMap
if $run_reproduction; then
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
            # Check if the a rupt_quads.txt file was created
            if [[ -f "${eventpath}/current/rupt_quads.txt" ]]; then
                mv ${eventpath}/current/rupt_quads.txt ${eventpath}/current/products/
            fi
            rm -r $eventpath/current
        fi
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


#############################################
#          Unconstrained ShakeMap           #
#############################################
# Check if the user wants to run the pointsource ShakeMap
if $run_unconstrained; then
    echo "[INFO] Running unconstrained workflow"

    if [[ -f "$eventpath/ffsimmer_pointsource/products/rupt_quads.txt" ]]; then
        echo "ffsimmer_pointsource is complete. Skipping."
    else
        ## Check if the ffsimmer_pointsource directory is complete
        if [[ -f "$eventpath/ffsimmer_pointsource/products/rupt_quads.txt" ]]; then
            echo "[INFO] ffsimmer_pointsource is complete. Skipping."
        else
            echo "[INFO] Running ffsimmer_pointsource"
            if [[ -d "$eventpath/ffsimmer_pointsource" ]]; then
                echo "Directory ffsimmer_pointsource already exists. Deleting ffsimmer_pointsource directory."
                rm -r $eventpath/ffsimmer_pointsource
            fi
            echo "[INFO] Running Point Source comparison shakemap..."
            mkdir $eventpath/ffsimmer_pointsource
            cp -r $eventpath/sm_create_input/event.xml $eventpath/ffsimmer_pointsource/
            ln -s $eventpath/ffsimmer_pointsource $eventpath/current
            shake $eventid select assemble -c "test" model contour mapping info gridxml raster >& $eventpath/current/log.txt
            mv ${eventpath}/current/rupt_quads.txt ${eventpath}/current/products/
            mv ${eventpath}/current/log.txt ${eventpath}/current/products/log.txt
            rm -r $eventpath/current
        fi
    fi

fi

#############################################
#           Constrained ShakeMap            #
#############################################
# Check if the user wants to run the constrained ShakeMaps
if $run_constrained; then
    if [[ -f "$eventpath/np1/products/rupt_quads.txt" ]]; then
        echo "[INFO] NP1 is complete. Skipping."
    else
        echo "[INFO] Running both NP1 and NP2 solutions..."
        ## Prep NP1 and NP2 configuration files
        read NP1_STRIKE NP1_DIP NP1_RAKE \
                NP2_STRIKE NP2_DIP NP2_RAKE \
                < <(python "${softpath}get-moment-tensor/getMomentTensor.py" "${eventid}" "${eventpath}" )
        echo "NP1 strike, dip rake: $NP1_STRIKE $NP1_DIP $NP1_RAKE"

        # Create model.conf file, set the number of simulations
        FFSIM_NSIM=20
        FFSIM_TRUE_GRID=True

        python ${softpath}/write_model_conf.py \
            --outfile "${eventpath}/np1_model.conf" \
            --nsim "$FFSIM_NSIM" \
            --true-grid "$FFSIM_TRUE_GRID" \
            --strike "$NP1_STRIKE" \
            --dip "$NP1_DIP"

        python ${softpath}/write_model_conf.py \
            --outfile "${eventpath}/np2_model.conf" \
            --nsim "$FFSIM_NSIM" \
            --true-grid "$FFSIM_TRUE_GRID" \
            --strike "$NP2_STRIKE" \
            --dip "$NP2_DIP"

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

    fi
fi

## Get region dimensions from both rupt_quad.txt files
REGION=$(python /Users/hyin/soft/shakemap-postprocess-tools/calc-region_rupt_quads.py --rq ${eventpath}/np1/products/rupt_quads.txt ${eventpath}/np2/products/rupt_quads.txt)
echo "Using region: ${REGION}"

# write the region to a file for later use
echo "${REGION}" > ${eventpath}/region.txt