#!/usr/bin/env python

import argparse
from array import array

import numpy as np
import pandas as pd

import ROOT


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",
                        help="The input csv file")
    parser.add_argument("-o", "--output",
                        help="Output root file to be written")
    parser.add_argument("--debug-mode",
                        action="store_true",
                        help="Write out debug output")
    return parser.parse_args()


def read_csv(infile):
    def _read_csv(infile, name):
        df= pd.read_csv(infile,
                            usecols=["{}.X".format(name), "{}.Y".format(name)])
        df.sort_values(by=["{}.X".format(name)], inplace=True)
        x_vals = df["{}.X".format(name)][pd.notnull(df["{}.X".format(name)])].values
        y_vals = df["{}.Y".format(name)][pd.notnull(df["{}.X".format(name)])].values
        return x_vals, y_vals
    exp_x, exp_y = _read_csv(infile, "exp0")
    obs_x, obs_y = _read_csv(infile, "obs")
    return (exp_x, exp_y), (obs_x, obs_y)


def convert_to_tgraph(xvals, yvals):
    if xvals.shape != yvals.shape:
        raise RuntimeError("X- and y-values do not share the same shape")
    graph = ROOT.TGraph(xvals.size, xvals, yvals)
    return graph


def create_tgraph2d(name, comp_graph):
    xarray = np.arange(130, 800, 1)
    yarray = np.arange(0.4, 10.1, 0.1)
    # Get minimum x value of graph to set
    # limits to fixed value for these points
    xlow = min(xval for i, xval in zip(xrange(comp_graph.GetN()), comp_graph.GetX()))
    xvals = []
    yvals = []
    zvals = []
    for xval in xarray:
        for yval in yarray:
            y_int = comp_graph.Eval(xval)
            c = 0.5
            alpha = 0.05
            a = alpha / c
            b = - alpha * (y_int - c) / c
            xvals.append(xval)
            yvals.append(yval)
            zvals.append(max(0, min(1, a * yval + b)) if xval > xlow else 0.5)
    np_x, np_y, np_z = array("d", xvals), array("d", yvals), array("d", zvals)
    graph = ROOT.TGraph2D(name, name,
                          len(xvals),
                          np_x, np_y, np_z)
    return graph


def main(args):
    exp, obs = read_csv(args.input)
    exp_graph = convert_to_tgraph(*exp)
    obs_graph = convert_to_tgraph(*obs)
    if args.debug_mode:
        out_debug = ROOT.TFile("debug_output.root", "recreate")
        exp_graph.Write("exp0")
        obs_graph.Write("obs")
        out_debug.Close()
    outfile = ROOT.TFile(args.output, "recreate")
    exp_2d = create_tgraph2d("exp0", exp_graph)
    obs_2d = create_tgraph2d("obs", obs_graph)
    outfile.Write()
    outfile.Close()
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
