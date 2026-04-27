#!/usr/bin/env python3

import argparse
from pathlib import Path

def write_model_conf(outfile, nsim, true_grid, strike, dip):
    content = f"""[modeling]
    ffsim_nsim = {nsim}
    ffsim_true_grid = {true_grid}
    ffsim_min_strike = {strike}
    ffsim_max_strike = {strike}
    ffsim_min_dip = {dip}
    ffsim_max_dip = {dip}
"""
    Path(outfile).write_text(content)
    print(f"Wrote {outfile}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outfile", required=True)
    parser.add_argument("--nsim", type=int, required=True)
    parser.add_argument("--true-grid", required=True)
    parser.add_argument("--strike", type=float, required=True)
    parser.add_argument("--dip", type=float, required=True)

    args = parser.parse_args()

    write_model_conf(
        args.outfile,
        args.nsim,
        args.true_grid,
        args.strike,
        args.dip,
    )

if __name__ == "__main__":
    main()