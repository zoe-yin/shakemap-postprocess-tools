#!/usr/bin/env python


import json
import pathlib
import sys
from datetime import datetime

import requests

EVENT_URL_TEMPLATE = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/detail/{eventid}.geojson"
)

print("test")

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

if __name__ == "__main__":
    eventid = sys.argv[1]
    outdir = pathlib.Path(sys.argv[2])
    if not outdir.exists():
        outdir.mkdir(parents=True)
    event_dict, moment_dict = get_moment_tensor(eventid)
    event_file = outdir / f"{eventid}_event.json"
    moment_file = outdir / f"{eventid}_tensor.json"
    print(f"Writing event data to {event_file}")
    with open(event_file, "wt") as fobj:
        event_dict["time"] = event_dict["time"].isoformat()
        json.dump(event_dict, fobj)

    if moment_dict is not None:
        print(f"Writing moment tensor data to {moment_file}")
        with open(moment_file, "wt") as fobj:
            json.dump(moment_dict, fobj)
