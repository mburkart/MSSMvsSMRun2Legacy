#!/usr/bin/env python

import argparse
import json
from math import floor
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
from plotting.utility import plot_limits

import ROOT

lumi_dict = {
    "2016": r"$35.9 \, \mathrm{fb}^{-1}$ (2016, 13 TeV)",
    "2017": r"$41.5 \, \mathrm{fb}^{-1}$ (2017, 13 TeV)",
    "2018": r"$59.7 \, \mathrm{fb}^{-1}$ (2018, 13 TeV)",
    "combined": r"$138 \, \mathrm{fb}^{-1}$ (13 TeV)",
}

# channel_dict = {
#     "mt": r"$\mu \tau_{h}$",
#     "et": r"$e \tau_{h}$",
#     "tt": r"$\tau_{h} \tau_{h}$",
#     "em": r"$e \mu$",
#     "cmb": "cmb",
# }
cont_dict = {
    "obs": "Observed",
    "exp0": "Median Expected",
    "exp-1": "16 % Expected",
    "exp-2": "2.5 % Expected",
    "exp+1": "84 % Expected",
    "exp+2": "97.5 % Expected",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",
                        type=str,
                        help="Input file."
    )
    parser.add_argument("-p", "--poi",
                        type=str,
                        help="The POI considered in the fits."
    )
    parser.add_argument("-m", "--mass",
                        type=str,
                        help="Mass of the considered signal."
    )
    parser.add_argument("-a", "--asymptotics-file",
                        type=str,
                        help="Root file containing results from Asymptotics."
    )
    parser.add_argument("-s", "--skip-limit-calculation",
                        action="store_true",
                        help="Skip calculation of limits from scanned points")
    return parser.parse_args()


def read_hybrid_cls(infile, poi, mass,
              res_type="obs"):
    """Read fit results from grid to calculate CLs values.

    The code is inspired by the grid readout from the HybridNew algorithm of combine.
    """
    toy_grid = {}
    # Get the directory where the results of the toys are stored in.
    toy_dir = infile.Get("toys")

    # Loop over all toys stored in the file and get the value of the POI
    # from their names and store the results to get the CLs values.
    num_appends=defaultdict(int)
    for key_name in set(key.GetName() for key in toy_dir.GetListOfKeys()):
        if key_name.startswith("HypoTestResult_mh"):
            # Key with correct naming found. Remove everything in front of
            # considered POI value from name
            key_name_red = key_name.replace("HypoTestResult_mh{}_{}".format(mass, poi), "")
        else:
            continue
        poi_val = float(key_name_red.split("_")[0])
        # TODO: Check if we want to skip POI if out of range
        # Get toy result
        toy = toy_dir.Get(key_name)
        # Append to toy result if it is already in grid.
        if poi_val not in toy_grid:
            toy_grid[poi_val] = toy
        else:
            toy_grid[poi_val].Append(toy)
            num_appends[poi_val]+=1
        toy_grid[poi_val].ResetBit(1)
    print(toy_grid)
    print(num_appends)

    # Loop over POI values from grid and calculate CLs and CLsErr from toys.
    res_grid = {}
    for poi, hyp_res in toy_grid.items():
        # There is no need to save and restore the value of the test statistics
        # as done in the LimitGrids.py script as we do not use the result further
        if "exp" in res_type:
            # Get distribution of background toys to calculate the quantile for the CLs
            # derivation for expected results
            btoys = sorted([x for x in hyp_res.GetNullDistribution().GetSamplingDistribution()])
            quantile = ROOT.Math.normal_cdf(float(res_type.replace("exp", "")))
            # Get test statistics from considered quantile
            testStat = btoys[int(min(floor(quantile * len(btoys) +0.5), len(btoys)-1))]
            hyp_res.SetTestStatisticData(testStat)
        # Now the calculation of the CLs value is the same for observed and expected.
        res_grid[poi] =  {"CLs": hyp_res.CLs(), "CLsErr": hyp_res.CLsError()}
        hyp_res.Print()
    return res_grid


def read_asymptotic_cls(infile,
                     res_type="obs"):
    """Read fit results from asymptotics calculation.

    All observed limit results from the given root file are read by
    scanning over the values in the tree.
    """
    res_cls = {}
    limit_tree = infile.Get("limit")
    for i in range(limit_tree.GetEntries()):
        limit_tree.GetEntry(i)
        quant_dict = {
                "exp0": 0.5,
                "exp-1": 0.84,
                "exp-2": 0.975,
                "exp+1": 0.16,
                "exp+2": 0.025,
                # "exp-1": 0.16,
                # "exp-2": 0.025,
                # "exp+1": 0.84,
                # "exp+2": 0.975,
        }
        # Find entries in tree that correspond to observed limits.
        # For these entries the value of quantileExpected is set to -1.
        if "exp" not in res_type and limit_tree.quantileExpected == -1:
            if limit_tree.r in res_cls:
                print("Two results for the same value of the POI found. "
                      "This should not happen...")
                raise ValueError
            else:
                res_cls[limit_tree.r] = limit_tree.limit
        for quantile, val in quant_dict.items():
            if quantile in res_type and abs(limit_tree.quantileExpected - val) < 1e-5:
                if limit_tree.r in res_cls:
                    print("Two results for the same value of the POI found. "
                          "This should not happen...")
                    raise ValueError
                else:
                    res_cls[limit_tree.r] = limit_tree.limit
    return res_cls


def calculate_limit_from_cls(r_vals, cls_vals):
    CLs = 0.05
    # First, find points were crossing happens.
    # Assume that CLs values decrease with increasing POI value
    right_index = 0
    for i, cls in enumerate(cls_vals):
        if cls <= 0.05:
            # Found the point where crossing happens
            right_index = i
            # If it is between two points interpolate between the points
            # to find crossing.
            # Else, extrapolate from last two points in range.
            if right_index == 0:
                # First value already below criterion
                # Shift index to the right.
                right_index = 1
            break
        elif cls > 0.05 and i == len(cls_vals) - 1:
            # No crossing in scanned points found.
            # Setting index anyway.
            right_index = i
            break
    # Calculate the slope from the two points
    slope = ((cls_vals[right_index] - cls_vals[right_index-1]) /
             (r_vals[right_index] -  r_vals[right_index-1]))
    intercept = cls_vals[right_index] - slope * r_vals[right_index]
    limit = ((CLs - cls_vals[right_index-1] + slope*r_vals[right_index-1]) /
             slope)
    return limit, lambda x: slope * x + intercept, (r_vals[right_index-1], r_vals[right_index])


def plot_cls_comparison(poi_vals, hybrid_res, hybrid_unc, asymp_res,
                        poi_name="r_bbH", mass="2900", contour="obs",
                        interpolation=None, int_range=None):
    # Create figure to plot on
    fig, ax = plt.subplots(figsize=(6., 6.))
    ax.errorbar(poi_vals, hybrid_res, yerr=hybrid_unc,
                label="toy-based", fmt="o")
    ax.plot(poi_vals, asymp_res, "s",
            label="asymptotic")

    # Plot interpolation if it is given.
    if interpolation is not None:
        r_range = np.linspace(*int_range, 50)
        ax.plot(r_range, interpolation(r_range),
                ls="-", label="toy-based interpolation",
                color="gray")

    ax.axhline(0.05, ls="-", color="red", alpha=0.75)
    ax.text(1., 0.7, "Exclusion at 95% CL",
            transform=ax.transAxes, fontsize=12,
            color="red",
            horizontalalignment="right")

    ax.set_xlabel(r"$\sigma(\mathrm{{{proc}}})\cdot\mathrm{{BR}}(\phi\rightarrow\tau\tau)$ [pb]".format(proc=poi_name.split("_")[-1]),
                  loc="right", fontsize=16)
    ax.set_ylabel(r"$\mathrm{CL}_{\mathrm{S}}$",
                  loc="top", fontsize=16)

    ax.set_ylim([1e-4, 1.])
    ax.set_yscale("log")

    ax.xaxis.set_minor_locator(AutoMinorLocator(5))
    ax.tick_params(which="both", direction="in",
                   bottom=True, top=True,
                   left=True, right=True)
    ax.tick_params(which="major",
                   length=6)
    ax.tick_params(which="minor",
                   length=3)

    ax.text(1., 0.8, r"$\mathrm{{m}}_{{\phi}} = {} \, \mathrm{{GeV}}$".format(mass),
            transform=ax.transAxes, fontsize=12,
            horizontalalignment="right")

    ax.text(0., 1.02, cont_dict[contour], transform=ax.transAxes, fontsize=12)
    ax.text(1., 1.02, lumi_dict["combined"], transform=ax.transAxes, horizontalalignment="right", fontsize=12)

    ax.legend(loc="upper right")
    fig.savefig("_".join([poi_name, mass, contour]) + ".png")
    return


def main(args):
    hybrid_limits = {}
    asymp_limits = {}
    for cont in ["obs", "exp0", "exp-1", "exp-2", "exp+1", "exp+2"]:
        infile = ROOT.TFile(args.input, "read")
        hybrid_res = read_hybrid_cls(infile, args.poi, args.mass, res_type=cont)
        print(json.dumps(hybrid_res, sort_keys=True, indent=4))

        asymp_file = ROOT.TFile(args.asymptotics_file, "read")
        asymp_res = read_asymptotic_cls(asymp_file, res_type=cont)
        print(json.dumps(asymp_res, sort_keys=True, indent=4))

        # Restructure result dicts in numpy arrays for plotting.
        poi_vals = np.array(list(sorted(map(float, hybrid_res.keys()))))
        hybrid_cls = np.array([item["CLs"] for _, item in sorted(hybrid_res.items(), key=lambda x: float(x[0]))])
        hybrid_clserr = np.array([item["CLsErr"] for _, item in sorted(hybrid_res.items(), key=lambda x: float(x[0]))])
        asymp_cls = np.array([cls for _, cls in sorted(asymp_res.items(), key=lambda x: float(x[0]))])

        print(poi_vals, hybrid_cls, hybrid_clserr, asymp_cls)
        if not args.skip_limit_calculation:
            hybrid_limits[cont], interp, rrange = calculate_limit_from_cls(poi_vals, hybrid_cls)
            asymp_limits[cont], _, _ = calculate_limit_from_cls(poi_vals, asymp_cls)
        else:
            interp, rrange = None, None
        # Create the comparison plot
        plot_cls_comparison(poi_vals, hybrid_cls, hybrid_clserr, asymp_cls,
                            poi_name=args.poi, mass=args.mass,
                            contour=cont,
                            interpolation=interp,
                            int_range=rrange)
    print(json.dumps(hybrid_limits, indent=4))
    print(json.dumps(asymp_limits, indent=4))
    if not args.skip_limit_calculation:
        # Build combined dict with asymptotic and toy based results
        # and write it to a file
        with open("limits_{}_{}.json".format(args.poi, args.mass), "w") as fi:
            json.dump({"asymptotic": asymp_limits,
                       "hybrid": hybrid_limits},
                      fi,
                      indent=4)
        plot_limits(hybrid_limits, asymp_limits,
                    "limits_{}_{}.png".format(args.poi, args.mass),
                    proc=args.poi.split("_")[1][0:-1],
                    mass=args.mass)
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
