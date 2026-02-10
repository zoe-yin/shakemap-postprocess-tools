#!/bin/bash

# Given a list of eventids's, this script will download the corresponding FSP files 
# and generate rupture.txt files for each event using the shakemap_polygon.py script.

array=(
    us2000d7q6
    us1000h3p4
    ak018fcnsk91
    # us2000jlfv
    # us60003sc0
    # ci38457511
    # us60007idc
    # us70007pa9
    # us6000ah9t
    # us7000c7y0
    # us6000dher
    # us7000e54r
    # ak0219neiszm
    # us6000f65h
    # us7000f93v
    # us6000h519
    # us6000i5rd
    # us7000i9bw
    # us6000jllz
    # us6000jlqa
    # us7000jvl3
    # us7000lff4
    # us6000m0xl
    # us7000lsze
    # us7000m9g4
    # us6000nith
    # us7000nzf3
    # us6000pi9w
    # us7000pn9s
    # us7000qdyl
    # us6000qw60
    # us7000qx2g
    # us6000rtdt
)

catalogdir='/Users/hyin/usgs_mendenhall/ffsimmer/catalog/ffsimmer-catalog-results/'

fsp_file='/Users/hyin/soft/shakemap-postprocess-tools/comcat-search/us6000dher/us6000dher_us_1_complete_inversion.fsp'
output_dir='/Users/hyin/soft/shakemap-postprocess-tools/comcat-search/us6000dher/'


for eventid in "${array[@]}"
do
	echo "$eventid"
    eventpath='/Users/hyin/shakemap_profiles/default/data/'${eventid}/
    getproduct finite-fault "complete_inversion.fsp" -i ${eventid} -o ${eventpath}
    fsp_file="${eventpath}/${eventid}_us_1_complete_inversion.fsp"   # us6000dher_us_1_complete_inversion.fsp
    echo "Generated FSP file: ${fsp_file}"
    python /Users/hyin/soft/shakemap-postprocess-tools/shakemap_polygon.py ${eventid} ${fsp_file} ${eventpath}
    echo "Generated rupture.txt file for event ${eventid} at ${eventpath}/rupture.txt" 
done


