#!/usr/bin/env python

import argparse
import json
import pathlib
import shutil
import os
from datetime import datetime

from configobj import ConfigObj
from esi_utils_rupture.origin import write_event_file

PROFILE_CONF = pathlib.Path.home() / ".shakemap" / "profiles.conf"


def get_data_path():
    config = ConfigObj(str(PROFILE_CONF))
    return pathlib.Path(config["profiles"][config["profile"]]["data_path"])


def get_station_data(stationfile):
    sdict = {}
    with open(stationfile, "rt") as fobj:
        jdict = json.load(fobj)
        sdict["type"] = jdict["type"]
        sdict["references"] = jdict["references"]
        sdict["features"] = []
        for feature in jdict["features"]:
            if feature["properties"]["station_type"] == "seismic":
                sdict["features"].append(feature)
    return sdict


def get_info_event(info_file):
    # - id (str, "us2008abcd")
    # - netid (str, "us")
    # - network (str, "USGS National Network")
    # - lat (float, 42.1234)
    # - lon (float, -85.1234)
    # - depth (float, 24.1)
    # - mag (float, 7.9)
    # - time (HistoricTime object)
    # - locstring (str, "East of the Poconos")
    # - mech (str, "RS", "SS", "NM", or 'ALL') (optional)
    # - reference (str, data source: 'Smith et al. 2016') (optional)
    # - event_type (str, 'ACTUAL' or 'SCENARIO') (optional)
    # - productcode (str, 'us2000wxyz_zoom')
    # - reviewed (str, 'true' or 'false' or 'unknown') (optional)

    event = {}
    with open(info_file, "rt") as fobj:
        jdict = json.load(fobj)
        event["id"] = jdict["input"]["event_information"]["event_id"]
        event["netid"] = jdict["input"]["event_information"]["eventsource"]
        event["network"] = ""
        event["lat"] = float(jdict["input"]["event_information"]["latitude"])
        event["lon"] = float(jdict["input"]["event_information"]["longitude"])
        event["depth"] = float(jdict["input"]["event_information"]["depth"])
        event["mag"] = float(jdict["input"]["event_information"]["magnitude"])
        event["time"] = datetime.fromisoformat(
            jdict["input"]["event_information"]["origin_time"].replace("Z", "")
        )
        event["locstring"] = jdict["input"]["event_information"]["location"]
        event["mech"] = jdict["input"]["event_information"]["src_mech"]
        event["reference"] = jdict["input"]["event_information"]["event_ref"]
        event["event_type"] = jdict["input"]["event_information"]["event_type"]
        event["product_code"] = jdict["input"]["event_information"]["productcode"]
        # if "origin_reviewed" not in jdict:
        #     event["reviewed"] = None
        # else:
        #     event["reviewed"] = jdict["input"]["event_information"]["origin_reviewed"] # @todo: this field doesn't show up in some events (e.g. us6000jllz v02)

    return event


def main():
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument(
        "folder", help="Directory where getproduct output was downloaded."
    )
    parser.add_argument("eventid", help="Desired eventid to extract to ShakeMap.")
    
    parser.add_argument(
        "version", type=int, help="Desired version to extract to ShakeMap."
    )
    parser.add_argument(
        "-n", "--no-dyfi", action="store_true", default=False, help="Turn off DYFI"
    )
    args = parser.parse_args()
    data_path = get_data_path()
    # Check if no_dyfi is set
    if args.no_dyfi:
        event_path = data_path / args.eventid / f"official_v{args.version:02}_no-dyfi"
    else:
        event_path = data_path / args.eventid / f"official_v{args.version:02}"
    if not event_path.exists():
        event_path.mkdir(parents=True)
    input_folder = pathlib.Path(args.folder) # / args.eventid
    for file in input_folder.glob("*.json"):
        # print(f"File: {str(file)}")
        parts = file.with_suffix("").name.split("_")
        version = int(parts[2]) 
        ftype = parts[3]    # check the filetype 
        # print(f"ftype: {str(ftype)}, version: {str(version)}")
        if version != args.version: # Check the version matches the specified one
            continue
        if ftype == "stationlist":
            print("Working on stationlist.json ...")
            station_data = {}
            if args.no_dyfi:
                print(f"DYFI data is being discarded...")
                station_data = get_station_data(file)
                file_name, file_extension = os.path.splitext(file.name)
                outfile = f"{event_path}/{file_name}_no-dyfi{file_extension}"
                print(f"Writing {outfile}...")
                with open(outfile, "wt") as fobj:
                    json.dump(station_data, fobj)
                if os.path.isfile(f"{event_path}/instrumented_dat.json"):
                    os.remove(f"{event_path}/instrumented_dat.json")
                os.symlink(outfile, f"{event_path}/instrumented_dat.json")
            else:
                print(f"Writing {file.name} to {event_path}")
                shutil.copy(file, event_path)

        elif ftype == "info":
            print("Working on event.xml...")
            event_data = get_info_event(file)
            outfile = event_path / "event.xml"
            print(f"Writing {outfile}...")
            # print(str(event_data))
            write_event_file(event_data, outfile)
        elif ftype == "rupture":
            print(f"Writing {file.name} to {event_path}")
            shutil.copy(file, event_path)
            if os.path.isfile(f"{event_path}/rupture.json"):
                os.remove(f"{event_path}/rupture.json")
            os.symlink(f"{event_path}/{file.name}", f"{event_path}/rupture.json")


if __name__ == "__main__":
    main()
