#!/usr/bin/env python

import os
import argparse
import logging
logger = logging.getLogger("")

import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True

import Dumbledraw.dumbledraw as dd
import CombineHarvester.CombineTools.plotting as limitplot


ll_dict = {
    "et":  "e#tau_{h}",
    "mt":  "#mu#tau_{h}",
    "tt":  "#tau_{h}#tau_{h}",
    "em":  "e#mu",
    "cmb": "combined",
    "combined": "combined (138 fb^{-1})",
    "2016": "2016 (36.3 fb^{-1})",
    "2017": "2017 (41.5 fb^{-1})",
    "2018": "2018 (59.7 fb^{-1})",
    "hig-17-020": "JHEP 09 (2018) 007", # 35.9 fb^{-1}
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dir",
                        required=True,
                        help="Directory with inputs")
    return parser.parse_args()


def setup_logging(output_file, level=logging.DEBUG):
    logger.setLevel(level)
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    file_handler = logging.FileHandler(output_file, "w")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def main(args):
    # Create the plot window we are interested in
    width = 600
    dummy_hist = ROOT.TH1F("dummy", "dummy", 1, 60, 3500)
    for proc in ["gg", "bb"]:
        plot = dd.Plot([0.0], "ModTDR", r=0.04, l=0.14, width=600)
        infile = os.path.join(args.input_dir,
                              "significance_ind",
                              "condor",
                              "mssm_{}H_p-value_condor.json".format(proc))
        # cols = ["#fd7f7f", "#73b0d5", "#b2e061", "#ffb55a"]
        cols = ["#ea5545", "#edbf33", "#87bc45", "#27aeef"]
        lcolors = list(map(ROOT.TColor.GetColor, cols)) + [ROOT.kBlack]
        plot.add_hist(dummy_hist, "dummy", "dummy")
        plot.setGraphStyle(dummy_hist, "axis")
        plot.add_graph(limitplot.StandardLimitsFromJSONFile(infile, "obs")["obs"], "significance", "significance")
        plot.setGraphStyle("significance", "pl",
                           linecolor=lcolors[0],
                           linestyle=2,
                           linewidth=2,
                           markercolor=lcolors[0],
                           markershape=20)
        plot.scaleYTitleSize(1.45)
        plot.scaleXTitleSize(1.45)
        plot.subplot(0).setLogX()
        plot.subplot(0).setLogY()
        plot.subplot(0).setYlims(5e-4, 1.1)
        plot.subplot(0).setXlims(60, 3500)
        plot.subplot(0).get_hist("dummy").GetXaxis().SetNoExponent()
        plot.subplot(0).get_hist("dummy").GetXaxis().SetMoreLogLabels()

        # Add axis labels
        plot.subplot(0).setXlabel("m_{#phi} (GeV)")
        plot.subplot(0).setYlabel("Local p-value")


        # plot.subplot(0).Draw(["dummy", "significance"])
        plot.subplot(0).Draw(["dummy"])

        # Add lines for one, two and three sigma
        line = ROOT.TLine()
        line.SetLineColor(ROOT.TColor.GetColor("#a9a9a9"))
        line.SetLineWidth(2)
        line.SetLineStyle(3)
        line.SetHorizontal()
        line.DrawLine(60, ROOT.RooStats.SignificanceToPValue(1),
                      3500, ROOT.RooStats.SignificanceToPValue(1))
        line.DrawLine(60, ROOT.RooStats.SignificanceToPValue(2),
                      3500, ROOT.RooStats.SignificanceToPValue(2))
        line.DrawLine(60, ROOT.RooStats.SignificanceToPValue(3),
                      3500, ROOT.RooStats.SignificanceToPValue(3))
        # Draw signficance by hand to properly draw it above sigma lines
        plot.subplot(0)._pad.cd()
        sig_graph = plot.subplot(0).get_graph("significance")
        sig_graph[0].Draw("{} same".format(sig_graph[2]))
        ROOT.gPad.RedrawAxis()

        # plot.add_legend(width=0.3, height=0.3)
        # plot.legend(0).setNColumns(1)
        # plot.legend(0).add_entry(0, "significance", "significance", "pl")
        # plot.legend(0).scaleTextSize(1.45)
        # plot.legend(0).Draw()

        plot.DrawLumi("#font[62]{CMS} data 138 fb^{-1} (13 TeV)")
        # plot.DrawChannelCategoryLabel("#font[42]{Expected}", begin_left=None)
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextAngle(0)
        latex.SetTextColor(ROOT.kBlack)
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.145, 0.955, "#font[42]{{{}#phi production}}".format(proc))
        latex.SetNDC(False)
        latex.SetTextSize(0.03)
        latex.SetTextColor(ROOT.TColor.GetColor("#a9a9a9"))
        latex.SetTextFont(42)
        latex.SetTextAlign(31)
        latex.DrawLatex(3200, 1.1*ROOT.RooStats.SignificanceToPValue(1), "1#kern[0.22]{s}.d.")
        latex.DrawLatex(3200, 1.1*ROOT.RooStats.SignificanceToPValue(2), "2#kern[0.22]{s}.d.")
        latex.DrawLatex(3200, 1.1*ROOT.RooStats.SignificanceToPValue(3), "3#kern[0.22]{s}.d.")

        plot.save(os.path.join(args.input_dir, "significance_ind", "model-indep-significance_{}H.png".format(proc)))
        plot.save(os.path.join(args.input_dir, "significance_ind", "model-indep-significance_{}H.pdf".format(proc)))
        plot.save(os.path.join(args.input_dir, "significance_ind", "model-indep-significance_{}H.C".format(proc)))
    return


if __name__ == "__main__":
    args = parse_args()
    setup_logging("plot_limits_by_channel.log", logging.INFO)
    main(args)
