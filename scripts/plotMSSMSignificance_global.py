#!/usr/bin/env python

import os
import argparse
import logging
logger = logging.getLogger("")
import json
from array import array

import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True

import Dumbledraw.dumbledraw as dd
from Dumbledraw.styles import CreateTransparentColor
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


def create_hist(values):
    # hist = ROOT.TH1D("toy_distribution", "toy_distribution", 100, min(values), max(values))
    nbins = 90
    hist = ROOT.TH1D("toy_distribution", "toy_distribution", nbins, 0., 4.)
    for val in values:
        hist.Fill(val)
    # Get overflow bin and add it to last bin. Reset overflow bin content to keep
    # total number of events constant
    print(hist.Integral())
    hist.SetBinContent(nbins, hist.GetBinContent(nbins) + hist.GetBinContent(nbins+1))
    hist.SetBinContent(nbins+1, 0)
    print(hist.Integral())
    return hist


def get_hist_to_color(boundary, hist):
    hist_col = hist.Clone()
    # Set the contents of all bins below boundary to zero
    ibin = 1
    while (hist_col.GetBinLowEdge(ibin) < boundary and ibin <= hist_col.GetNbinsX()+1):
        # Save content of bin to be set to zero to be able to restore it later
        bin_c = hist_col.GetBinContent(ibin)
        hist_col.SetBinContent(ibin, 0)
        ibin += 1
    # Reset the bin boundary of the last bin that has been set to zero
    bins = [hist_col.GetBinLowEdge(i) for i in range(1, hist_col.GetNbinsX()+2)]
    bins[ibin-2] = boundary
    bins_arr = array("d", bins)
    hist_col.SetBins(len(bins)-1, bins_arr)
    # Restore bin content of bin of reduced size
    hist_col.SetBinContent(ibin-1, bin_c)
    return hist_col


def main(args):
    # Create the plot window we are interested in
    width = 600
    # dummy_hist = ROOT.TH1F("dummy", "dummy", 1, 60, 3500)
    plot = dd.Plot([0.0], "ModTDR", r=0.04, l=0.14, width=600)
    infile = "analysis_2022_02_28/model-indep_classic_2022-08-08_hSM-in-bg/global_significance/global_p-value_mH1200.json"
    # cols = ["#fd7f7f", "#73b0d5", "#b2e061", "#ffb55a"]
    cols = ["#ea5545", "#edbf33", "#87bc45", "#27aeef"]
    lcolors = list(map(ROOT.TColor.GetColor, cols)) + [ROOT.kBlack]
    with open(infile, "r") as fi:
        indict = json.load(fi)["1200.0"]
    hist = create_hist(indict["toys"])
    plot.add_hist(hist, "toys")
    plot.setGraphStyle("toys", "hist",
                       # linecolor=lcolors[0],
                       linecolor=ROOT.kBlack,
                       linestyle=1,
                       linewidth=2,
                       markercolor=lcolors[0],
                       markershape=20)
    # infi_loc = "local_p-value_mH1200.json"
    # with open(infi_loc, "r") as fi:
    #     indict_loc = json.load(fi)["1200.0"]
    # hist_loc = create_hist(indict_loc["toys"])
    # plot.add_hist(hist_loc, "toys_loc")
    # plot.setGraphStyle("toys_loc", "hist",
    #                    linecolor=ROOT.kRed,
    #                    linewidth=2)
    # plot.subplot(0).get_hist("dummy").GetXaxis().SetNoExponent()
    # plot.subplot(0).get_hist("dummy").GetXaxis().SetMoreLogLabels()
    sig_obs = float(indict["obs"][0])
    hist_col = get_hist_to_color(sig_obs, hist)
    plot.add_hist(hist_col, "toys_col")
    plot.setGraphStyle(
            "toys_col", "hist",
            linecolor=ROOT.kBlack,
            linestyle=1,
            linewidth=0,
            fillcolor=CreateTransparentColor(lcolors[0], 0.3)
            # fillcolor=CreateTransparentColor(ROOT.kRed+1, 0.3)
    )

    infile = "analysis_2022_02_28/model-indep_classic_2022-08-08_hSM-in-bg/global_significance/global_p-value_mH130.json"
    with open(infile, "r") as fi:
        indi_130 = json.load(fi)["130.0"]
        sig_obs_130 = float(indi_130["obs"][0])
        pval_130 = indi_130["p"]
        pval_unc_130 = indi_130["p_unc"]
    hist_col_130 = get_hist_to_color(sig_obs_130, hist)
    plot.add_hist(hist_col_130, "toys_col130")
    plot.setGraphStyle(
            "toys_col130", "hist",
            linecolor=ROOT.kBlack,
            linestyle=1,
            linewidth=0,
            fillcolor=CreateTransparentColor(lcolors[3], 0.3)
            # fillcolor=CreateTransparentColor(ROOT.kGreen+3, 0.3)
   )

    # hist_col.SetFillColorAlpha(r.kRed+1, 0.3)

    # Add axis labels
    plot.subplot(0).setXlabel("Maximum local significance #sigma_{max} (s.d.)")
    plot.subplot(0).setYlabel("Frequency (arb. u.)")

    # plot.subplot(0).Draw(["dummy", "significance"])
    plot.subplot(0).setYlims(0, hist.GetMaximum()*1.2)
    plot.subplot(0).Draw(["toys_col130", "toys_col", "toys"])
    ROOT.gPad.RedrawAxis()

    sig_ind = ROOT.TArrow(sig_obs, hist.GetMaximum()*0.25, sig_obs, 0+2, 0.03, "|>")
    sig_ind.SetAngle(40),
    sig_ind.SetLineWidth(3)
    sig_ind.SetLineColor(lcolors[0])
    sig_ind.SetFillColor(lcolors[0])
    # sig_ind.SetFillColor(ROOT.kBlack)
    sig_ind.Draw()
    sig_ind_130 = ROOT.TArrow(sig_obs_130, hist.GetMaximum()*0.25, sig_obs_130, 0+2, 0.03, "|>")
    sig_ind_130.SetAngle(40),
    sig_ind_130.SetLineWidth(3)
    sig_ind_130.SetLineColor(lcolors[3])
    sig_ind_130.SetFillColor(lcolors[3])
    # sig_ind_130.SetFillColor(ROOT.kBlack)
    sig_ind_130.Draw()

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
    latex.SetTextFont(42)
    latex.DrawLatex(0.145, 0.955, "{}#phi production".format("gg"))
    latex.SetTextSize(0.035)
    left = 0.62
    top = 0.85
    diff = 0.045
    latex.DrawLatex(left, top, "8000 toys")
    # latex.SetTextColor(ROOT.kGreen+3)
    latex.SetTextColor(lcolors[3])
    latex.DrawLatex(left, top-diff, "#font[52]{{p}}_{{#lower[-0.2]{{130 GeV}}}} = {:.3f}#pm{:.3f}".format(pval_130, pval_unc_130))
    # latex.SetTextColor(ROOT.kRed+1)
    latex.SetTextColor(lcolors[0])
    latex.DrawLatex(left+0.01, top-2*diff, "#font[52]{{p}}_{{#lower[-0.2]{{1.2 TeV}}}} = {:.3f}#pm{:.3f}".format(indict["p"], indict["p_unc"]))
    latex.SetTextSize(0.035)
    latex.SetNDC(False)
    latex.DrawLatex(2.87, 40., "#sigma_{#lower[-0.2]{1.2 TeV}}")
    latex.SetTextColor(lcolors[3])
    latex.SetTextAlign(31)
    latex.DrawLatex(2.53, 40., "#sigma_{#lower[-0.2]{130 GeV}}")
    # latex.DrawLatex(3200, 1.1*ROOT.RooStats.SignificanceToPValue(1), "1#kern[0.22]{s}.d.")
    # latex.DrawLatex(3200, 1.1*ROOT.RooStats.SignificanceToPValue(2), "2#kern[0.22]{s}.d.")
    # latex.DrawLatex(3200, 1.1*ROOT.RooStats.SignificanceToPValue(3), "3#kern[0.22]{s}.d.")

    plot.save(os.path.join(args.input_dir, "global_significance", "model-indep-significance_global_mH{}_v4_bfit.png".format(1200)))
    plot.save(os.path.join(args.input_dir, "global_significance", "model-indep-significance_global_mH{}_v4_bfit.pdf".format(1200)))
    plot.save(os.path.join(args.input_dir, "global_significance", "model-indep-significance_global_mH{}_v4_bfit.C".format(1200)))
    return


if __name__ == "__main__":
    args = parse_args()
    setup_logging("plot_limits_by_channel.log", logging.INFO)
    main(args)
