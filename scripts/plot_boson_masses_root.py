#!/usr/bin/env python

from array import array
import argparse

import numpy as np

import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True
import Dumbledraw.styles as styles

from CombineHarvester.MSSMvsSMRun2Legacy.mssm_xs_tools import mssm_xs_tools


mZ = 91.1876
mh = 125.38


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mode",
                        choices=["tree-level", "tanb"],
                        default="tanb",
                        help="Comparison mode")
    return parser.parse_args()


def tree_level_mh(mA, tanb):
    return np.sqrt(1/2. * (mA**2 + mZ**2 - np.sqrt((mA**2 + mZ**2)**2 - 4*mA**2*mZ**2*np.cos(2*np.arctan(tanb))**2)))


def tree_level_mH(mA, tanb):
    return np.sqrt(1/2. * (mA**2 + mZ**2 + np.sqrt((mA**2 + mZ**2)**2 - 4*mA**2*mZ**2*np.cos(2*np.arctan(tanb))**2)))


def create_tgraph(xarray, yarray):
    if len(xarray) != len(yarray):
        raise ValueError("Lengths of x and y array differ...")
    graph = ROOT.TGraph(len(xarray), array("d", xarray), array("d", yarray))
    return graph


def main(args):
    styles.ModTDRStyle(width=600, r=0.04, l=0.14)
    tanbs = [5., 10., 20.]

    mA_scan = np.linspace(70, 300, 47)

    mssm_inputs = mssm_xs_tools("data/mh125_13.root", False, 1)
    h_mass = []
    H_mass = []
    # Get masses of CP-even Higgs bosons for each tanb value
    for tanb in tanbs:
        h_mass_tanb = []
        H_mass_tanb = []
        for mA in mA_scan:
            h_mass_tanb.append(mssm_inputs.mass("h", mA, tanb))
            H_mass_tanb.append(mssm_inputs.mass("H", mA, tanb))
        h_mass.append(h_mass_tanb)
        H_mass.append(H_mass_tanb)

    # Add tree level predictions to plot
    mh_tree = tree_level_mh(mA_scan, 5.)
    mH_tree = tree_level_mH(mA_scan, 5.)

    # Start drawing of extracted masses. Starting from here the modes
    # will differ
    canv = ROOT.TCanvas()
    canv.SetTicks()
    graphs = []
    colours = [ROOT.TColor.GetColor("#1f77b4"),
               ROOT.TColor.GetColor("#ff7f0e"),
               ROOT.TColor.GetColor("#2ca02c")]
    linestyles = [1, 2, 3]

    dummy_hist = ROOT.TH1D("dummy", "dummy", 1, mA_scan[0], mA_scan[-1])
    # Make general adjustments of range and axis labels
    dummy_hist.GetYaxis().SetRangeUser(mA_scan[1]-20, mA_scan[-1]+20)
    dummy_hist.GetXaxis().SetTitle("m_{A} (GeV)")
    dummy_hist.GetYaxis().SetTitle("m_{h/H} (GeV)")
    dummy_hist.Draw("axis")
    # Translate diagonal in mA to graph and plot it
    graphs.append(create_tgraph(mA_scan, mA_scan))
    graphs[-1].SetLineWidth(2)
    graphs[-1].SetLineColor(ROOT.kGray+2)
    graphs[-1].SetLineStyle(2)
    graphs[-1].Draw("l same")

    graphs.append(create_tgraph(mA_scan, np.full(mA_scan.shape, mh)))
    graphs[-1].SetLineWidth(2)
    graphs[-1].SetLineColor(ROOT.kGray+2)
    graphs[-1].SetLineStyle(2)
    graphs[-1].Draw("l same")

    if args.mode == "tanb":
        for i, (tanb, h_masses, H_masses, col, ls) in enumerate(zip(tanbs, h_mass, H_mass, colours, linestyles)):
            graphs.append(create_tgraph(mA_scan, h_masses))
            graphs[-1].SetLineWidth(2)
            graphs[-1].SetLineColor(col)
            graphs[-1].SetLineStyle(ls)
            # if i == 0:
            #     graphs[-1].GetXaxis().SetRangeUser(mA_scan[0], mA_scan[-1])
            #     graphs[-1].GetYaxis().SetRangeUser(mA_scan[1]-20, mA_scan[-1]+20)
            #     graphs[-1].GetXaxis().SetTitle("m_{A} (GeV)")
            #     graphs[-1].GetYaxis().SetTitle("m_{h/H} (GeV)")
            #     graphs[-1].Draw("a l")
            # else:
            graphs[-1].Draw("l same")

            graphs.append(create_tgraph(mA_scan, H_masses))
            graphs[-1].SetLineWidth(2)
            graphs[-1].SetLineColor(col)
            graphs[-1].SetLineStyle(ls)
            graphs[-1].Draw("l same")
    elif args.mode == "tree-level":
        colours = [ROOT.TColor.GetColor("#1f77b4"),
                   ROOT.TColor.GetColor("#d62728")]
        for i, (h_masses, H_masses, col, ls) in enumerate(zip([h_mass[0], mh_tree], [H_mass[0], mH_tree],
                                                              colours[:2], [1, 3])):
            graphs.append(create_tgraph(mA_scan, h_masses))
            graphs[-1].SetLineWidth(2)
            graphs[-1].SetLineColor(col)
            graphs[-1].SetLineStyle(ls)
            # if i == 0:
            #     graphs[-1].GetXaxis().SetRangeUser(mA_scan[0], mA_scan[-1])
            #     graphs[-1].GetYaxis().SetRangeUser(mA_scan[1]-20, mA_scan[-1]+20)
            #     graphs[-1].GetXaxis().SetTitle("m_{A} (GeV)")
            #     graphs[-1].GetYaxis().SetTitle("m_{h/H} (GeV)")
            #     graphs[-1].Draw("a l")
            # else:
            graphs[-1].Draw("l same")

            graphs.append(create_tgraph(mA_scan, H_masses))
            graphs[-1].SetLineWidth(2)
            graphs[-1].SetLineColor(col)
            graphs[-1].SetLineStyle(ls)
            graphs[-1].Draw("l same")

    legend = ROOT.TLegend(0.16, 0.75, 0.42, 0.92)
    if args.mode == "tanb":
        for i, tanb in enumerate(tanbs):
            legend.AddEntry(graphs[2*i+2], "tan#kern[0.2]{{#beta}} = {:2d}".format(int(tanb)), "l")
    elif args.mode == "tree-level":
        legend.AddEntry(graphs[2], "M_{h}^{125} scenario prediction", "l")
        legend.AddEntry(graphs[4], "Tree-level prediction", "l")
    legend.SetTextSize(0.038)
    legend.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextAngle(0)
    latex.SetTextColor(ROOT.kBlack)
    if args.mode == "tanb":
        latex.SetTextSize(0.042)
        latex.DrawLatex(0.66, 0.87, "M_{h}^{125} scenario")
    elif args.mode == "tree-level":
        # latex.SetTextSize(0.042)
        # latex.DrawLatex(0.56, 0.87, "M_{h}^{125} scenario")
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.145, 0.955, "#font[42]{{tan#kern[0.2]{{#beta}} = {}}}".format(int(tanbs[0])))

    latex.SetTextSize(0.038)
    latex.DrawLatex(0.67, 0.70, "#font[42]{m_{H}}")
    latex.DrawLatex(0.67, 0.36, "#font[42]{m_{h}}")

    canv.Print("masses_mh125{}_root.png".format("_with_tree_level" if args.mode == "tree-level" else ""))
    canv.Print("masses_mh125{}_root.pdf".format("_with_tree_level" if args.mode == "tree-level" else ""))
    canv.Print("masses_mh125{}_root.C".format("_with_tree_level" if args.mode == "tree-level" else ""))

    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
