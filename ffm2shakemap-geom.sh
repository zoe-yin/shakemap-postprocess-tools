#!/bin/bash

array=(
    us6000dher
    us6000f65h
    us6000h519
    us70007pa9
    us7000i9bw
    us7000qdyl
    us7000qx2g
    us1000gcii
    us1000gez7
    us1000haa3
    us2000iyta
    us1000j96d
    us70003hqb
    us6000417i
    us70004jyv
    us60006bjl
    us6000ah9t  #
    us7000aq3e
    us6000c9hg
    us6000dg77
    us6000f48v
    us6000f9sq  #
    us6000gc2a
    us7000gymk
    us7000i7ya
    us7000ip0l
    us7000irfb
    us7000j553
    us6000k6mg
    us6000kd0n
    us7000l9h4
    us7000lgwp
    us6000n8tq
    us7000n05d
    us7000pntq
    us7000qvw5
)
for eventid in "${array[@]}"
do
	echo "$eventid"
    eventpath='/Users/hyin/shakemap_profiles/default/data/'${eventid}
    
    # Write FSP file to the ShakeMap event path
    getproduct finite-fault "complete_inversion.fsp" -i ${eventid} -d /Users/hyin/shakemap_profiles/default/data/

    # Convert FSP to rupt.json ShakeMap input file
    /Users/hyin/soft/shakemap-postprocess-tools/shakemap_polygon.py ${eventid} ${eventpath}/${eventid}*complete_inversion.fsp ${eventpath}/
    mv ${eventpath}/shakemap_polygon.txt ${eventpath}/shakemap_fault.txt

    # shake $eventid rupture

    # Optional: set up directory for re-run
    # rm ${eventpath}/shakemap_reproduction/rupture.json
    rm -r ${eventpath}/shakemap_reproduction/products
    
done
