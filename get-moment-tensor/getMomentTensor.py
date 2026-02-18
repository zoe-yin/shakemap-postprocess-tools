#!/usr/bin/env python


import json
import pathlib
import sys
from datetime import datetime

import requests

EVENT_URL_TEMPLATE = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{eventid}.geojson"
)

def get_moment_tensor(eventid):
    url = EVENT_URL_TEMPLATE.format(eventid=eventid)
    response = requests.get(url)
    if response.status_code != 200:
        msg = f"Could not retrieve any data from {url}"
        raise Exception(msg)
    jdict = response.json()
    lon, lat, depth = jdict["geometry"]["coordinates"]
    event_props = {
        "id": jdict["id"],
        "time": datetime.fromtimestamp(jdict["properties"]["time"] / 1000),
        "latitude": lat,
        "longitude": lon,
        "depth": depth,
        "location": jdict["properties"]["place"],
    }
    if "moment-tensor" not in jdict["properties"]["products"]:
        print(f"WARNING: Could not find moment tensor data for event {eventid}")
        return (event_props, None)

    return (event_props, jdict["properties"]["products"]["moment-tensor"][0])

def get_nps(file):
    """
    Takes a tensor.json file and calculates NP1 and NP2
    
    input: tensor.json file
    output: returns variables np1 and np2, each arrays with values [strike, dip, rake]
    """
    from obspy.imaging.beachball import MomentTensor, mt2plane, aux_plane

    with open(file) as f:
        d = json.load(f)
    if d['source'] == 'ci':
        # print("Reading California MT solution")
        props = d["properties"]
 
        # Extract tensor components (convert strings to float)
        mrr = float(props["tensor-mrr"])
        mtt = float(props["tensor-mtt"])
        mpp = float(props["tensor-mpp"])
        mrt = float(props["tensor-mrt"])
        mrp = float(props["tensor-mrp"])
        mtp = float(props["tensor-mtp"])
        # Order: Mrr, Mtt, Mpp, Mrt, Mrp, Mtp, random exponent to make the class happy
        mt = MomentTensor(mrr, mtt, mpp, mrt, mrp, mtp, 10)
        
        # # Compute nodal planes
        np1 = mt2plane(mt)
        np2 = aux_plane(np1.strike,np1.dip, np1.rake)
        np1 = (np1.strike,np1.dip,np1.rake)
        return np1, np2

    # if d['source'] == 'us':
    else: 
        props = d["properties"]
        np1 = (float(props["nodal-plane-1-strike"]), float(props["nodal-plane-1-dip"]), float(props["nodal-plane-1-rake"]))
        np2 = (float(props["nodal-plane-2-strike"]), float(props["nodal-plane-2-dip"]), float(props["nodal-plane-2-rake"]))
        return np1, np2
    

if __name__ == "__main__":
    eventid = sys.argv[1]
    outdir = pathlib.Path(sys.argv[2])
    if not outdir.exists():
        outdir.mkdir(parents=True)
    event_dict, moment_dict = get_moment_tensor(eventid)
    event_file = outdir / f"{eventid}_event.json"
    moment_file = outdir / f"{eventid}_tensor.json"
    # print(f"Writing event data to {event_file}")
    with open(event_file, "wt") as fobj:
        event_dict["time"] = event_dict["time"].isoformat()
        json.dump(event_dict, fobj)

    if moment_dict is not None:
        # print(f"Writing moment tensor data to {moment_file}")
        with open(moment_file, "wt") as fobj:
            json.dump(moment_dict, fobj)
    # Print Nodal Plane info
    np1, np2 = get_nps(moment_file)
    print(
        np1[0], np1[1], np1[2],
        np2[0], np2[1], np2[2],
    )
        
