#!/usr/bin/env python
import argparse
import json
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, PercentFormatter

from plotting.utility import lumi_dict


contours = {
        "obs": "Observed",
        "exp0": "Median expected",
}

poi_dict = {
        "r_ggH": r"gg$\phi$",
        "r_bbH": r"bb$\phi$",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dir",
                        type=str,
                        help="Directory containing the input json files")
    parser.add_argument("-p", "--poi",
                        type=str,
                        help="The POI considered in the fits."
    )
    return parser.parse_args()


def plot_limit_comparison(masses,
                          asymptotic_limits,
                          hybrid_limits,
                          poi="r_ggH"):
    fig, ax = plt.subplots(figsize=(6., 6.))

    for to_compare in ["obs", "exp0"]:
        asym_comp = np.array([lim[to_compare] for lim in asymptotic_limits])
        hybrid_comp = np.array([lim[to_compare] for lim in hybrid_limits])

        ax.plot(masses, (hybrid_comp - asym_comp)/asym_comp, "o:",
                label=contours[to_compare])

    ax.axhline(y=0., ls="--", color="grey")
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))
    ax.yaxis.set_major_formatter(PercentFormatter(xmax=1., decimals=0))
    ax.tick_params(which="both", direction="in",
                   bottom=True, top=True,
                   left=True, right=True)
    ax.tick_params(which="major",
                   length=6)
    ax.tick_params(which="minor",
                   length=3)

    ax.set_xlabel(r"$\mathrm{m}_{\phi}$ [GeV]",
                  loc="right", fontsize=16)
    ax.set_ylabel(r"Rel. diff. of hyb. and asym. limits $(\mathrm{L}_{\mathrm{h}}-\mathrm{L}_{\mathrm{a}})/\mathrm{L}_{\mathrm{a}}$",
                  loc="top", fontsize=16)

    ax.text(1., 1.02, lumi_dict["combined"],
            transform=ax.transAxes, horizontalalignment="right",
            fontsize=12)
    ax.text(0., 1.02, poi_dict[poi],
            transform=ax.transAxes, horizontalalignment="left",
            fontsize=12)
    ax.legend(loc="lower right")

    fig.savefig("limit_comparison_{}.png".format(poi))
    fig.savefig("limit_comparison_{}.pdf".format(poi))
    return


def plot_limit_comparison_normalized(
                          masses,
                          asymptotic_limits,
                          hybrid_limits,
                          poi="r_ggH"):
    fig, ax = plt.subplots(figsize=(6., 6.))
    colors = ["#ea5545", "#27aeef"]
    for to_compare, col in zip(["obs", "exp0"], colors):
        asym_comp_var_list = []
        for alim, hlim in zip(asymptotic_limits, hybrid_limits):
            asym_comp_var_list.append(alim["exp-1"] - alim["exp0"] if hlim[to_compare] > alim[to_compare] else alim["exp0"] - alim["exp+1"])
        asym_comp_var = np.array(asym_comp_var_list)
        asym_comp = np.array([lim[to_compare] for lim in asymptotic_limits])
        hybrid_comp = np.array([lim[to_compare] for lim in hybrid_limits])

        ax.plot(masses, (hybrid_comp - asym_comp)/(asym_comp_var), "o:",
                label=contours[to_compare], color=col)

    ax.axhline(y=0., ls="--", color="grey")
    ax.axhline(y=1., ls="--", color="grey")
    ax.axhline(y=-1., ls="--", color="grey")
    ax.set_ylim(-1.3, 1.3)
    ax.yaxis.set_minor_locator(AutoMinorLocator(5))
    # ax.yaxis.set_major_formatter(PercentFormatter(xmax=1., decimals=0))
    ax.tick_params(which="both", direction="in",
                   bottom=True, top=True,
                   left=True, right=True)
    ax.tick_params(which="major",
                   length=6)
    ax.tick_params(which="minor",
                   length=3)

    ax.set_xlabel(r"$\mathrm{m}_{\phi}$ (TeV)",
                  loc="right", fontsize=16)
    # ax.set_ylabel(r"Relative difference of hybrid from asymptotic",
    ax.set_ylabel(r"$(L_{\mathrm{e}}-L_{\mathrm{a}})/\sigma_{L_{\mathrm{a}}}$",
                  loc="top", fontsize=16)

    ax.text(1., 1.02, lumi_dict["combined"],
            transform=ax.transAxes, horizontalalignment="right",
            fontsize=12)
    ax.text(0., 1.02, "{} production".format(poi_dict[poi]),
            transform=ax.transAxes, horizontalalignment="left",
            fontsize=12)
    ax.legend(loc=(0.5, 0.13), frameon=False, fontsize=14)

    # fig.tight_layout()
    plt.subplots_adjust(top=0.94, bottom=0.12, left=0.14, right=0.96)

    fig.savefig("limit_comparison_{}_normalized.png".format(poi))
    fig.savefig("limit_comparison_{}_normalized.pdf".format(poi))
    return


def main(args):
    plt.style.use("modtdr")
    masses = [2300, 2600, 2900, 3200, 3500]
    asymptotic_limits = []
    hybrid_limits = []
    for mass in masses:
        with open(os.path.join(args.input_dir, "limits_{}_{}.json".format(args.poi, mass)) , "r") as fi:
            limits = json.load(fi)
            asymptotic_limits.append(limits["asymptotic"])
            hybrid_limits.append(limits["hybrid"])

    masses_arr = np.array(masses)/1000.
    plot_limit_comparison(
            masses_arr,
            asymptotic_limits,
            hybrid_limits,
            poi=args.poi)

    plot_limit_comparison_normalized(
            masses_arr,
            asymptotic_limits,
            hybrid_limits,
            poi=args.poi)
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
