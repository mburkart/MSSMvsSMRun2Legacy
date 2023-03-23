#!/usr/bin/env python

import json
import argparse
import os
from typing import List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",
                        type=str,
                        help="Impacts result json.")
    parser.add_argument("-p", "--process",
                        type=str,
                        help="Process the impacts are computed for.")
    parser.add_argument("-m", "--mass",
                        type=str,
                        help="Mass of the signal hypothesis")
    return parser.parse_args()


def collect_pulls(results: List):
    data = map(lambda x: (x["fit"][1], x["name"], x["fit"][0], x["fit"][2]), results)
    df = pd.DataFrame(data, columns=["diff", "name", "down", "up"])
    df["pull"] = 2 * df["diff"]/(df.up -df.down)
    return df


def gauss(x, norm=1., mean=0., sigma=1.):
    return norm/np.sqrt(2*np.pi*sigma*sigma) * np.exp(-(x-mean)*(x-mean)/(2*sigma*sigma))


def create_plot(dataframe, outname,
                df_add=None, to_plot="diff",
                mass="250", proc="r_ggH"):
    fig, ax = plt.subplots()
    # dataframe.plot.hist(ax=ax, bins=30, range=(-3,3))
    if df_add is None:
        n, _, _ = ax.hist(dataframe[to_plot], bins=30, range=(-3,3),
                          density=True,
                          label="pull")
    else:
        n, _, _ = ax.hist([dataframe[to_plot], df_add[to_plot]],
                          label=("MC stat. unc.", "Syst. unc."),
                          color=("#84a98c", "#cad2c5"),
                          # color=("#87bc45", "#edbf33"),
                          bins=30, range=(-3,3),
                          linewidth=1., edgecolor="black",
                          stacked=True,
                          density=True,
                          histtype="stepfilled")

    if to_plot == "pull":
        ax.set_xlabel("Pull (s.d.)")
    else:
        ax.set_xlabel(r"$(\hat{\theta}_{j}-\theta_{j, \mathrm{in}})/\sigma_{\theta_{j}, \mathrm{in}}$")
    ax.set_ylabel("Prob. Density (arb. u.)")

    # Draw gaussian as expected distribution.
    x = np.linspace(-3., 3., 600)
    if df_add is None:
        norm = len(dataframe.index)*0.2
    else:
        norm = (len(dataframe.index) + len(df_add.index))*0.2
    ax.plot(x, gauss(x, norm=1.),
                 "r", label=r"$\mathcal{N} (0, 1)$")

    ax.set_xlim(-3., 3.)
    ax.set_ylim(0, 1.2*np.max(n))
    ax.text(1., 1.02,
            r"$\bf{CMS}$ data $138 \, \mathrm{fb}^{-1}$ ($13 \, \mathrm{TeV}$)",
            transform=ax.transAxes, horizontalalignment="right", fontsize=12)

    ax.text(0.03, 0.93,
            r"$\mathrm{{m}}_{{\phi}}$ = ${} \, \mathrm{{GeV}}$".format(mass),
            transform=ax.transAxes, horizontalalignment="left", fontsize=12)
    ax.text(0., 1.02,
            r"$\mathrm{gg}\phi$ production" if proc == "r_ggH" else r"$\mathrm{bb}\phi$ production",
            transform=ax.transAxes, horizontalalignment="left", fontsize=12)
    # ax.text(0.05, 0.90,
    #         r"$\sigma(\mathrm{gg}\phi)\mathcal{B}(\phi\rightarrow\tau\tau)$ = $(-0.16 \pm 0.09) \, \mathrm{pb}$",
    #         transform=ax.transAxes, horizontalalignment="left", fontsize=12)

    handles, labels = ax.get_legend_handles_labels()
    print(handles, labels)
    plt_handles = reversed(handles) if df_add is None else [handles[i] for i in [1,2,0]]
    plt_labels = reversed(labels) if df_add is None else [labels[i] for i in [1,2,0]]
    ax.legend(plt_handles, plt_labels,
              loc="upper right", frameon=False,
              handlelength=1.5, handleheight=1.5,
              labelspacing=0.7)

    # fig.tight_layout()
    plt.subplots_adjust(top=0.94, bottom=0.12, left=0.14, right=0.96)
    fig.savefig(outname)
    fig.savefig(outname.replace(".png", ".pdf"))
    return None


def main(args):
    plt.style.use("modtdr")
    if not os.path.exists(args.input):
        print("Input file {} does not exist.".format(args.input))
        raise Exception

    with open(args.input, "r") as fi:
        input_js = json.load(fi)["params"]
    df = collect_pulls(input_js)

    # Create figure to contain the full plot.
    print("Outliers from full set of pulls:")
    print(df.loc[(df.pull < -3) | (df.pull > 3)])
    create_plot(df, "diff_{}_allParams_{}.png".format(args.process, args.mass),
                mass=args.mass)

    # Filter for bin-by-bin uncertainties.
    bbb_mask = df.name.str.startswith("prop")

    df_bbb = df.loc[bbb_mask]
    create_plot(df_bbb, "diff_{}_BinByBin_{}.png".format(args.process, args.mass),
                mass=args.mass, proc=args.process)

    df_nobbb = df.loc[~bbb_mask]
    create_plot(df_nobbb, "diff_{}_noBinByBin_{}.png".format(args.process, args.mass),
                mass=args.mass, proc=args.process)

    # Create stacked plot of bbb and nobbb nuisance parameters
    create_plot(df_bbb, "diff_{}_stacked_{}.png".format(args.process, args.mass),
                df_add=df_nobbb,
                mass=args.mass, proc=args.process)
    create_plot(df_bbb, "pulls_{}_stacked_{}.png".format(args.process, args.mass),
                df_add=df_nobbb, to_plot="pull",
                mass=args.mass, proc=args.process)
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
