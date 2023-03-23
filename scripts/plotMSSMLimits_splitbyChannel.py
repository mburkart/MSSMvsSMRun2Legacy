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
    parser.add_argument("-m", "--mode",
                        choices=["per-year", "per-channel"],
                        help="Split results by year or channel")
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


def get_ch_split_inputs(indir, channels, proc):
    return [os.path.join(indir, "datacards_bsm-model-indep",
                                "combined",
                                ch,
                                "mssm_{}H_{}.json".format(proc, ch))
                     for ch in channels]

def get_year_split_inputs(indir, years, proc):
    return [os.path.join(indir, "datacards_bsm-model-indep",
                                year,
                                "cmb",
                                "mssm_{}H_cmb.json".format(proc))
                     for year in years]


def main(args):
    # Create the plot window we are interested in
    width = 600
    channels = ["em", "et", "mt", "tt", "cmb"]
    years = ["2016", "2017", "2018", "combined"]
    dummy_hist = ROOT.TH1F("dummy", "dummy", 1, 60, 3500)
    for proc in ["gg", "bb"]:
        plot = dd.Plot([0.0], "ModTDR", r=0.04, l=0.14, width=600)
        if args.mode == "per-channel":
            inp_files = get_ch_split_inputs(args.input_dir, channels, proc)
            # cols = ["#fd7f7f", "#73b0d5", "#b2e061", "#ffb55a"]
            cols = ["#ea5545", "#edbf33", "#87bc45", "#27aeef"]
            lstyles = [2, 2, 2, 2, 1]
            mstyles = [21, 22, 23, 34, 20]
            lcolors = list(map(ROOT.TColor.GetColor, cols)) + [ROOT.kBlack]
        else:
            inp_files = [os.path.join(os.getcwd(),
                                      "mssm_limits_HIG-17-020",
                                      "HIG-17-020_{}Hout.json".format(proc))]
            inp_files.extend(get_year_split_inputs(args.input_dir, years, proc))
            cols = ["#ea5545", "#edbf33", "#27aeef"]
            lstyles = [1, 2, 2, 2, 1]
            mstyles = [20, 21, 22, 23, 20]
            lcolors = [ROOT.TColor.GetColor("#a9a9a9")] + list(map(ROOT.TColor.GetColor, cols)) + [ROOT.kBlack]
        plot.add_hist(dummy_hist, "dummy", "dummy")
        plot.setGraphStyle(dummy_hist, "axis")
        if args.mode == "per-channel":
            names = channels
        else:
            names = ["hig-17-020"] + years
        for fi, name, col, lst, mst in zip(inp_files, names, lcolors, lstyles, mstyles):
            plot.add_graph(limitplot.StandardLimitsFromJSONFile(fi, "exp0")["exp0"], name, name)
            plot.setGraphStyle(name, "pl",
                               linecolor=col,
                               linestyle=lst,
                               linewidth=2,
                               markercolor=col,
                               markershape=mst)
        plot.scaleYTitleSize(1.45)
        plot.scaleXTitleSize(1.45)
        plot.subplot(0).setLogX()
        plot.subplot(0).setLogY()
        plot.subplot(0).setYlims(1e-4, 1e2)
        plot.subplot(0).setXlims(60, 3500)
        plot.subplot(0).get_hist("dummy").GetXaxis().SetNoExponent()
        plot.subplot(0).get_hist("dummy").GetXaxis().SetMoreLogLabels()

        # Add axis labels
        plot.subplot(0).setXlabel("m_{#phi} (GeV)")
        plot.subplot(0).setYlabel("95% CL limit on #sigma#font[42]{{({}#phi)}}#font[52]{{B}}#font[42]{{(#phi#rightarrow#tau#tau)}} (pb)".format(proc))


        plot.subplot(0).Draw(["dummy"] + names)

        plot.add_legend(width=0.3 if args.mode == "per-channel" else 0.4, height=0.3)
        plot.legend(0).setNColumns(1)
        if args.mode == "per-channel":
            for ch in reversed(channels):
                plot.legend(0).add_entry(0, ch, ll_dict[ch], "pl")
        else:
            for year in reversed(["hig-17-020"] + [y for y in reversed(years) if y != "combined"] + ["combined"]):
                plot.legend(0).add_entry(0, year, ll_dict[year], "pl")
        plot.legend(0).scaleTextSize(1.45)
        plot.legend(0).Draw()

        if args.mode == "per-channel":
            plot.DrawLumi("#font[62]{CMS} data 138 fb^{-1} (13 TeV)")
        else:
            plot.DrawLumi("#font[62]{CMS} data (13 TeV)")
        # plot.DrawChannelCategoryLabel("#font[42]{Expected}", begin_left=None)
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextAngle(0)
        latex.SetTextColor(ROOT.kBlack)
        latex.SetTextSize(0.04)
        latex.DrawLatex(0.145, 0.955, "#font[42]{Median Expected}")

        plot.save("model-indep-limits_{}H_{}.png".format(proc, args.mode))
        plot.save("model-indep-limits_{}H_{}.pdf".format(proc, args.mode))
        plot.save("model-indep-limits_{}H_{}.C".format(proc, args.mode))
    return


if __name__ == "__main__":
    args = parse_args()
    setup_logging("plot_limits_by_channel.log", logging.INFO)
    main(args)
