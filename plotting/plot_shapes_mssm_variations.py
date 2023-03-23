#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

import Dumbledraw.dumbledraw as dd
#import Dumbledraw.rootfile_parser_inputshapes as rootfile_parser
import Dumbledraw.rootfile_parser as rootfile_parser
import Dumbledraw.styles as styles

import argparse
import copy
import yaml
import os
from array import array

import logging
logger = logging.getLogger("")

name_dict = {
    "CMS_htt_doublemutrg": "#tau#tau bkg. norm. (4%)",
    "CMS_scale_met_emb": "#vec{p}_{T}^{#kern[0.1]{m}iss} unc.",
    "CMS_eff_t_emb_30-35_2016": "#tau Id. eff. [30,35]",
    "CMS_eff_t_emb_35-40_2016": "#tau Id. eff. [35,40]",
    "CMS_eff_t_emb_40-500_2016": "#tau Id. eff. [40,100]",
    "CMS_eff_t_emb_highpT_100-500_2016": "#tau Id. eff. [100,500]",
    "CMS_eff_t_emb_highpT_500-inf_2016": "#tau Id. eff. [100,#infty)",
    "CMS_scale_t_emb_1prong1pizero_2016": "#tau ES #pi^{#pm}#pi^{0}(#pi^{0})",
    "CMS_htt_emb_ttbar_2016": "#tau#tau bkg. t#bar{t} contr.",
}


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=
        "Plot categories using Dumbledraw from shapes produced by shape-producer module."
    )
    parser.add_argument(
        "-l", "--linear", action="store_true", help="Enable linear x-axis")
    parser.add_argument(
        "-c",
        "--channels",
        nargs="+",
        type=str,
        required=True,
        help="Channels")
    parser.add_argument("-e", "--era", type=str, required=True, help="Era")
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="ROOT file with shapes of processes")
    parser.add_argument(
        "--control-variable",
        type=str,
        default=None,
        help="Enable plotting goodness of fit shapes for given variable")
    parser.add_argument(
        "--png", action="store_true", help="Save plots in png format")
    parser.add_argument(
        "--normalize-by-bin-width",
        action="store_true",
        help="Normelize plots by bin width")
    parser.add_argument(
        "--fake-factor",
        action="store_true",
        help="Fake factor estimation method used")
    parser.add_argument(
        "--embedding",
        action="store_true",
        help="Fake factor estimation method used")
    parser.add_argument(
        "-o", "--output-dir",
        help="Output directory for the plots.")
    parser.add_argument(
        "--control-region",
        action="store_true",
        help="Skip signal categories")
    parser.add_argument(
        "--blinded",
        action="store_true",
        help="Do not draw data.")
    parser.add_argument(
        "--x-range",
        type=lambda xranges: [float(edge) for edge in xranges.split(',')],
        default=None,
        help="Smaller x-range used in the plot to zoom into problematic regions")
    parser.add_argument(
        "--combine-backgrounds",
        action="store_true",
        help="Combine minor backgrounds to single shape")
    parser.add_argument(
        "--up-variation",
        type=str,
        default=None,
        help="Add total background shape of up-variation of unc in ratio plot."
    )
    parser.add_argument(
        "--down-variation",
        type=str,
        default=None,
        help="Add total background shape of down-variation of unc in ratio plot."
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        help="The name of the drawn uncertainty"
    )
    parser.add_argument(
        "--lowmass",
        action="store_true",
        help="Plots for lowmass part of analysis"
    )
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


def rebin_hist_for_logX(hist, xlow=1.0):
    bins = []
    contents= []
    errors = []
    # Get low bin edges, contents and errors of all bins.
    for i in range(1, hist.GetNbinsX()+1):
        bins.append(hist.GetBinLowEdge(i))
        contents.append(hist.GetBinContent(i))
        errors.append(hist.GetBinError(i))
    # Add low edge of overflow bin as high edge of last regular bin.
    bins.append(hist.GetBinLowEdge((hist.GetNbinsX()+1)))
    # Check if first bin extents to zero and if it does change it to larger value
    if bins[0] == 0.:
        bins[0] = xlow
    # Create the new histogram
    bin_arr = array("f", bins)
    hist_capped = ROOT.TH1F(hist.GetName(), hist.GetTitle(), len(bin_arr)-1, bin_arr)
    for i in range(0, hist_capped.GetNbinsX()):
        hist_capped.SetBinContent(i+1, contents[i])
        hist_capped.SetBinError(i+1, errors[i])
    return hist_capped


def main(args):
    if args.up_variation is None and args.down_variation is not None:
        raise RuntimeError("Specifying only down variation is not supported.")
    elif args.up_variation is not None and args.down_variation is None:
        raise RuntimeError("Specifying only up variation is not supported.")
    if args.control_variable is None:
        channel_categories = {
            #"et": ["nobtag_tightmt", "nobtag_loosemt", "btag_tightmt", "btag_loosemt"]
            "et": ["32", "33",  "35", "36"],
            #"mt": ["nobtag_tightmt", "nobtag_loosemt", "btag_tightmt", "btag_loosemt"]
            "mt": ["32", "33",  "35", "36"],
            #"tt": ["nobtag", "btag"]
            "tt": ["32", "35"],
            "em": ["2","32", "33", "34", "35", "36", "37"]
        }
        if args.lowmass:
            channel_categories = {
                "mt": ["132", "232", "332", "432", "35"],
                "et": ["132", "232", "332", "432", "35"],
                "tt": ["132", "232", "332", "432", "35"],
                "em": ["132", "133", "232", "233", "332", "333", "432", "433", "35", "36"],
            }
    else:
        channel_categories = {
            "et": ["100"],
            "mt": ["100"],
            "tt": ["100"],
            "em": ["100"]
        }
    channel_dict = {
        "ee": "ee",
        "em": "e#mu",
        "et": "e#tau_{h}",
        "mm": "#mu#mu",
        "mt": "#mu#tau_{h}",
        "lt": "#mu#tau_{h}+e#tau_{h}",
        # "lt": "#ell#tau_{h}",
        "tt": "#tau_{h}#tau_{h}"
    }
    if args.control_variable is None:
        category_dict = {
            "et": {
                "32": "No b tag, Tight-m_{T}",
                "33": "No b tag, Loose-m_{T}",
                "132": "No b tag, p_{T}^{#tau#tau} < 50 GeV",
                "232": "No b tag, 50 < p_{T}^{#tau#tau} < 100 GeV",
                "332": "No b tag, 100 < p_{T}^{#tau#tau} < 200 GeV",
                "432": "No b tag, 200 GeV < p_{T}^{#tau#tau}",
                "35": "b tag, Tight-m_{T}",
                "36": "b tag, Loose-m_{T}",
                },
            "mt": {
                "32": "No b tag, Tight-m_{T}",
                "33": "No b tag, Loose-m_{T}",
                "132": "No b tag, p_{T}^{#tau#tau} < 50 GeV",
                "232": "No b tag, 50 < p_{T}^{#tau#tau} < 100 GeV",
                "332": "No b tag, 100 < p_{T}^{#tau#tau} < 200 GeV",
                "432": "No b tag, 200 GeV < p_{T}^{#tau#tau}",
                "35": "b tag, Tight-m_{T}",
                "36": "b tag, Loose-m_{T}",
                },
            "lt": {
                "32": "No b tag, Tight-m_{T}",
                "33": "No b tag, Loose-m_{T}",
                "132": "No b tag, p_{T}^{#tau#tau} < 50 GeV",
                "232": "No b tag, 50 < p_{T}^{#tau#tau} < 100 GeV",
                "332": "No b tag, 100 < p_{T}^{#tau#tau} < 200 GeV",
                "432": "No b tag, 200 GeV < p_{T}^{#tau#tau}",
                "35": "b tag, Tight-m_{T}",
                "36": "b tag, Loose-m_{T}",
                },
            "tt": {
                "32": "No b tag",
                "132": "No b tag, p_{T}^{#tau#tau} < 50 GeV",
                "232": "No b tag, 50 < p_{T}^{#tau#tau} < 100 GeV",
                "332": "No b tag, 100 < p_{T}^{#tau#tau} < 200 GeV",
                "432": "No b tag, 200 GeV < p_{T}^{#tau#tau}",
                "35": "b tag",
                },
            "em": {
                "2": "d_{#lower[-0.2]{#zeta}} < -35 GeV",
                "32": "No b tag, High-D_{#lower[-0.2]{#zeta}}",
                "33": "No b tag, Medium-D_{#lower[-0.2]{#zeta}}",
                "34": "No b tag, Low-D_{#lower[-0.2]{#zeta}}",
                "132": "No b tag, -D_{#lower[-0.2]{#zeta}}, p_{T}^{#tau#tau} < 50 GeV",
                "232": "No b tag, -D_{#lower[-0.2]{#zeta}}, 50 < p_{T}^{#tau#tau} < 100 GeV",
                "332": "No b tag, -D_{#lower[-0.2]{#zeta}}, 100 < p_{T}^{#tau#tau} < 200 GeV",
                "432": "No b tag, -D_{#lower[-0.2]{#zeta}}, 200 GeV < p_{T}^{#tau#tau}",
                "35": "b tag, High-D_{#lower[-0.2]{#zeta}}",
                "36": "b tag, Medium-D_{#lower[-0.2]{#zeta}}",
                "37": "b tag, Low-D_{#lower[-0.2]{#zeta}}",
                },

        }
    else:
        category_dict = {"100": "inclusive"}
    if args.linear == True:
        split_value = 0
    else:
        if args.normalize_by_bin_width:
            split_value = 1
        else:
            split_value = 101

    split_dict = {c: split_value for c in ["et", "mt", "tt", "em", "lt"]}

    bkg_processes = [
        "HSM", "VVL", "TTL", "ZL", "jetFakes", "EMB"
    ]
    if args.combine_backgrounds:
        bkg_processes = [
            "other", "TTL", "jetFakes", "EMB"
        ]
    if not args.fake_factor and args.embedding:
        bkg_processes = [
            "QCD", "VVJ", "VVL", "W", "TTJ", "TTL", "ZJ", "ZL", "EMB"
        ]
    if not args.embedding and args.fake_factor:
        bkg_processes = [
            "VVT", "VVJ", "TTT", "TTJ", "ZJ", "ZL", "jetFakes", "ZTT"
        ]
    if not args.embedding and not args.fake_factor:
        bkg_processes = [
            "QCD", "W", "VVJ", "VVL", "VVT", "TTJ", "TTL", "TTT", "ZJ", "ZL", "ZTT"
#            "QCD", "VVT", "VVJ", "W", "TTT", "TTJ", "ZJ", "ZL", "ZTT"
        ]
    all_bkg_processes = [b for b in bkg_processes]
    legend_bkg_processes = copy.deepcopy(bkg_processes)
    legend_bkg_processes.reverse()

    if "2016" in args.era:
        era = "2016"
    elif "2017" in args.era:
        era = "2017"
    elif "2018" in args.era:
        era = "2018"
    elif "combined" in args.era:
        era = ""
    else:
        logger.critical("Era {} is not implemented.".format(args.era))
        raise Exception

    plots = []
    for channel in args.channels:
        if "em" in channel:
            if not args.embedding:
                bkg_processes = [
                    "HSM", "QCDMC", "VVT", "VVL", "W", "TTT", "TTL", "ZL", "ZTT"
                ]
            else:
                bkg_processes = [
                    "HSM", "QCD", "EWK", "TTL", "ZL", "EMB"
                ]
                if args.combine_backgrounds:
                    bkg_processes = [
                        "other", "QCD", "TTL", "EMB"
                    ]

        for category in channel_categories[channel]:
            # Set split value to 101 for no b-tag categories to make
            # transition between scales smoother
            if int(category) < 35 and int(category) > 10:
                split_dict[channel] += 100
            if args.control_region and category != "2":
                continue
            print(args.input)
            rootfile = rootfile_parser.Rootfile_parser(args.input, mode="CombineHarvester")
            legend_bkg_processes = copy.deepcopy(bkg_processes)
            legend_bkg_processes.reverse()
            # create plot
            if args.linear == True:
                plot = dd.Plot(
                    [0.3, [0.3, 0.28]], "ModTDR", r=0.04, l=0.14, width=600)
            else:
                plot = dd.Plot(
                    [0.50, [0.3, 0.28]], style="ModTDR", invert_pad_creation=True, r=0.04, l=0.14, width=600)

            # get background histograms
            for process in bkg_processes:
                if process in ["jetFakes", "jetFakesEMB"] and channel == "tt":
                    jetfakes_hist = rootfile.get(era, channel, category, process).Clone("jetFakesComb")
                    jetfakes_hist.Add(rootfile.get(era, channel, category, "wFakes"))
                    if not args.lowmass:
                        jetfakes_hist = rebin_hist_for_logX(jetfakes_hist, xlow=30.)
                    plot.add_hist(jetfakes_hist, process, "bkg")
                elif process in ["HSM"]:
                    if channel == "em":
                        hsm_hist = rootfile.get(era, channel, category, "ggH125").Clone("H125")
                        hsm_hist.Add(rootfile.get(era, channel, category, "qqH125"))
                        hsm_hist.Add(rootfile.get(era, channel, category, "bbH125"))
                        hsm_hist.Add(rootfile.get(era, channel, category, "ggHWW125"))
                        hsm_hist.Add(rootfile.get(era, channel, category, "qqHWW125"))
                        hsm_hist.Add(rootfile.get(era, channel, category, "ZHWW125"))
                        hsm_hist.Add(rootfile.get(era, channel, category, "WHWW125"))
                        if not args.lowmass:
                            hsm_hist = rebin_hist_for_logX(hsm_hist, xlow=30.)
                        plot.add_hist(hsm_hist, process, "bkg")
                    else:
                        hsm_hist = rootfile.get(era, channel, category, "ggH125").Clone("H125")
                        hsm_hist.Add(rootfile.get(era, channel, category, "qqH125"))
                        hsm_hist.Add(rootfile.get(era, channel, category, "bbH125"))
                        if not args.lowmass:
                            hsm_hist = rebin_hist_for_logX(hsm_hist, xlow=30.)
                        plot.add_hist(hsm_hist, process, "bkg")
                elif process == "EWK" and channel == "em":
                    ewk_hist = rootfile.get(era, channel, category, "W").Clone("EWK")
                    ewk_hist.Add(rootfile.get(era, channel, category, "VVL"))
                    if not args.lowmass:
                        ewk_hist = rebin_hist_for_logX(ewk_hist, xlow=30.)
                    plot.add_hist(ewk_hist, process, "bkg")
                elif process in ["HWW"]:
                    hww_hist = rootfile.get(era, channel, category, "ggHWW125").Clone("HWW")
                    hww_hist.Add(rootfile.get(era, channel, category, "qqHWW125"))
                    hww_hist.Add(rootfile.get(era, channel, category, "ZHWW125"))
                    hww_hist.Add(rootfile.get(era, channel, category, "WHWW125"))
                    if not args.lowmass:
                        hww_hist = rebin_hist_for_logX(hww_hist, xlow=30.)
                    plot.add_hist(hww_hist, process, "bkg")
                elif process == "other":
                    if channel == "em":
                        other_hist = rootfile.get(era, channel, category, "W").Clone("other")
                        other_hist.Add(rootfile.get(era, channel, category, "VVL"))
                        other_hist.Add(rootfile.get(era, channel, category, "ZL"))
                        other_hist.Add(rootfile.get(era, channel, category, "ggH125"))
                        other_hist.Add(rootfile.get(era, channel, category, "qqH125"))
                        other_hist.Add(rootfile.get(era, channel, category, "bbH125"))
                        other_hist.Add(rootfile.get(era, channel, category, "ggHWW125"))
                        other_hist.Add(rootfile.get(era, channel, category, "qqHWW125"))
                        other_hist.Add(rootfile.get(era, channel, category, "ZHWW125"))
                        other_hist.Add(rootfile.get(era, channel, category, "WHWW125"))
                        if not args.lowmass:
                            other_hist = rebin_hist_for_logX(other_hist, xlow=30.)
                        plot.add_hist(other_hist, process, "bkg")
                    elif channel in ["et", "mt", "lt", "tt"]:
                        other_hist = rootfile.get(era, channel, category, "VVL").Clone("other")
                        other_hist.Add(rootfile.get(era, channel, category, "ZL"))
                        other_hist.Add(rootfile.get(era, channel, category, "ggH125"))
                        other_hist.Add(rootfile.get(era, channel, category, "qqH125"))
                        other_hist.Add(rootfile.get(era, channel, category, "bbH125"))
                        if not args.lowmass:
                            other_hist = rebin_hist_for_logX(other_hist, xlow=30.)
                        plot.add_hist(other_hist, process, "bkg")
                else:
                    #print era, channel, category, process
                    if args.lowmass:
                        plot.add_hist(
                            rootfile.get(era, channel, category, process), process, "bkg")
                    else:
                        plot.add_hist(
                            rebin_hist_for_logX(
                                rootfile.get(era, channel, category, process),
                                xlow=30.),
                            process, "bkg")
                plot.setGraphStyle(
                    process, "hist", fillcolor=styles.color_dict[process])

            if int(category.split("_")[0]) > 30:
                plot_idx_to_add_signal = [0,2] if args.linear else [1,2]
                for i in plot_idx_to_add_signal:
                    ggH_hist = rootfile.get(era, channel, category, "ggh_t").Clone("ggh")
                    ggH_hist.Add(rootfile.get(era, channel, category, "ggh_i"))
                    ggH_hist.Add(rootfile.get(era, channel, category, "ggh_b"))
                    if not args.lowmass:
                        ggH_hist = rebin_hist_for_logX(ggH_hist, xlow=30.)
                    plot.subplot(i).add_hist(ggH_hist, "ggH")

            # get observed data and total background histograms
            if args.lowmass:
                plot.add_hist(
                    rootfile.get(era, channel, category, "data_obs"), "data_obs")
                plot.add_hist(
                    rootfile.get(era, channel, category, "TotalBkg"), "total_bkg")
            else:
                plot.add_hist(
                    rebin_hist_for_logX(
                        rootfile.get(era, channel, category, "data_obs"),
                        xlow=30.),
                    "data_obs")
                plot.add_hist(
                    rebin_hist_for_logX(
                        rootfile.get(era, channel, category, "TotalBkg"),
                        xlow=30.),
                    "total_bkg")

            plot.subplot(0).setGraphStyle("data_obs", "e0")
            plot.setGraphStyle(
                "total_bkg",
                "e2",
                markersize=0,
                fillcolor=styles.color_dict["unc"],
                linecolor=0)
            if int(category.split("_")[0]) > 30:
                color = styles.color_dict["ggH"] if args.lowmass else styles.color_dict["bbH"]
                plot.subplot(0 if args.linear else 1).setGraphStyle(
                    "ggH", "hist", linecolor=color, linewidth=2)

            # assemble ratio
            to_normalize = ["total_bkg", "data_obs"]
            if args.up_variation is not None:
                rootfile_up = rootfile_parser.Rootfile_parser(args.up_variation, mode="CombineHarvester")
                rootfile_down = rootfile_parser.Rootfile_parser(args.down_variation, mode="CombineHarvester")
                if args.lowmass:
                    plot.add_hist(
                        rootfile_up.get(era, channel, category, "TotalBkg"), "total_bkg_up")
                else:
                    plot.add_hist(
                        rebin_hist_for_logX(
                            rootfile_up.get(era, channel, category, "TotalBkg"),
                            xlow=30.),
                        "total_bkg_up")
                plot.setGraphStyle(
                    "total_bkg_up", "hist", linecolor=ROOT.kGray+3,
                    linewidth=2, linestyle=2)
                if args.lowmass:
                    plot.add_hist(
                        rootfile_down.get(era, channel, category, "TotalBkg"), "total_bkg_down")
                else:
                    plot.add_hist(
                        rebin_hist_for_logX(
                            rootfile_down.get(era, channel, category, "TotalBkg"),
                            xlow=30.),
                        "total_bkg_down")
                plot.setGraphStyle(
                    "total_bkg_down", "hist", linecolor=ROOT.kGray+3,
                    linewidth=2, linestyle=3)
                to_normalize.extend(["total_bkg_up", "total_bkg_down"])
            # Add signal also to normalized lower panel
            if int(category.split("_")[0]) > 30:
                bkg_ggH = plot.subplot(2).get_hist("ggH")
                bkg_ggH.Add(plot.subplot(2).get_hist("total_bkg"))
                plot.subplot(2).add_hist(bkg_ggH, "bkg_ggH")
                color = styles.color_dict["ggH"] if args.lowmass else styles.color_dict["bbH"]
                plot.subplot(2).setGraphStyle(
                    "bkg_ggH",
                    "hist",
                    linecolor=color,
                    linewidth=2)
                to_normalize.append("bkg_ggH")
            plot.subplot(2).normalize(to_normalize, "total_bkg")

            # stack background processes
            plot.create_stack(bkg_processes, "stack")

            # Use binning from data histogram to get bin widths for the normalization.
            hist_for_rebinning = rootfile.get(era, channel, category, "data_obs")
            widths = []
            if not args.lowmass:
                for i in range(hist_for_rebinning.GetNbinsX()):
                    widths.append(hist_for_rebinning.GetBinWidth(i+1))
            # normalize stacks by bin-width
            if args.normalize_by_bin_width:
                if args.lowmass:
                    plot.subplot(0).normalizeByBinWidth()
                    plot.subplot(1).normalizeByBinWidth()
                else:
                    plot.subplot(0).normalizeByBinWidth(widths=widths)
                    plot.subplot(1).normalizeByBinWidth(widths=widths)

            if args.x_range is not None:
                for i in range(3):
                    plot.subplot(i).setXlims(*args.x_range)

            # set axes limits and labels
            if args.x_range is not None:
                range_hist = plot.subplot(0).get_hist("data_obs").Clone()
                range_hist.GetXaxis().SetRangeUser(*args.x_range)
                plot.subplot(0).setYlims(
                    split_dict[channel],
                    max(1.33 * range_hist.GetMaximum(),
                        split_dict[channel] * 2))
                    # max(1,
                    #     split_dict[channel] * 2))
            else:
                if args.lowmass:
                    max_scale = 1.6
                else:
                    max_scale = 1.8
                plot.subplot(0).setYlims(
                    split_dict[channel],
                    max(max_scale * plot.subplot(0).get_hist("data_obs").GetMaximum(),
                        split_dict[channel] * 2))

            if args.lowmass:
                plot.subplot(2).setYlims(0.9, 1.2)
                if int(category) > 400:
                    plot.subplot(2).setYlims(0.8, 1.35)
            else:
                plot.subplot(2).setYlims(0.7, 2.2)

            if not args.linear:
                # plot.subplot(1).setYlims(1.e-4, split_dict[channel])
                plot.subplot(1).setYlims(min(1.e-3, plot.subplot(1).get_hist("data_obs").GetMinimum()/10., plot.subplot(1).get_hist("total_bkg").GetMinimum()/10.), split_dict[channel])
                plot.subplot(1).setLogY()
                if int(category) > 30 or int(category) == 2:
                    plot.subplot(1).setLogX()
                plot.subplot(1).setYlabel(
                    "")  # otherwise number labels are not drawn on axis
            if args.control_variable != None:
                if args.control_variable in styles.x_label_dict[args.channels[0]]:
                    x_label = styles.x_label_dict[args.channels[0]][
                        args.control_variable]
                else:
                    x_label = args.control_variable
                plot.subplot(2).setXlabel(x_label)
            elif args.lowmass:
                if int(category) == 2:
                    plot.subplot(2).setXlabel("m_{T}^{tot} (GeV)")
                else:
                    plot.subplot(2).setXlabel("m_{#tau#tau} (GeV)")
            else:
                if int(category) > 30 or int(category) == 2:
                    plot.subplot(2).setXlabel("m_{T}^{tot} (GeV)")
                else:
                    plot.subplot(2).setXlabel("SVFit m_{#tau#tau} (GeV)")
            if args.normalize_by_bin_width:
                if (int(category) > 30 and not args.lowmass) or int(category) == 2:
                    plot.subplot(0).setYlabel("dN/dm_{T}^{tot} (1/GeV)")
                    # plot.subplot(0).setYlabel("< Events / GeV >")
                else:
                    plot.subplot(0).setYlabel("dN/dm_{#tau#tau} (1/GeV)")
            else:
                plot.subplot(0).setYlabel("Events / {} GeV".format(plot.subplot(0).get_hist("total_bkg").GetBinWidth(1)))

            plot.subplot(2).setYlabel("Obs./Exp.")


            if (int(category) > 30 or int(category) == 2) and args.x_range is None and not args.lowmass:
                plot.subplot(0).setLogX()
                plot.subplot(2).setLogX()
            elif args.lowmass and int(category) == 2:
                plot.subplot(0).setLogX()
                plot.subplot(2).setLogX()

            plot.scaleYLabelSize(0.8)
            plot.scaleYTitleOffset(1.05)

            if channel == "em":
                if category == "32":
                    plot.subplot(0).setNYdivisions(3, 5)
                elif category == "33":
                    plot.subplot(0).setNYdivisions(4, 5)
            if int(category) < 35 and int(category) > 10:
                plot.subplot(1).setNYdivisions(3, 5)
            plot.subplot(2).setNYdivisions(3, 5)

            # draw subplots. Argument contains names of objects to be drawn in corresponding order.
            # procs_to_draw = ["stack", "total_bkg", "ggH", "ggH_top", "bbH", "bbH_top", "data_obs"] if args.linear else ["stack", "total_bkg", "data_obs"]
            procs_to_draw = ["stack", "total_bkg", "ggH", "total_bkg_up", "total_bkg_down", "data_obs"] if args.linear else ["stack", "total_bkg", "ggH", "total_bkg_up", "total_bkg_down", "data_obs"]
            if args.blinded:
                procs_to_draw.remove("data_obs")
            plot.subplot(0).Draw(procs_to_draw)
            if not args.linear:
                # plot.subplot(1).Draw([
                #     "stack", "total_bkg", "ggH", "bbH",
                #     "ggH_top", "bbH_top",
                #     "data_obs"
                # ])
                if category == "2":
                    plot.subplot(1).Draw([
                        "stack", "total_bkg",
                        "data_obs"
                    ])
                else:
                    procs_to_draw = ["stack", "total_bkg", "ggH", "data_obs"]
                    if args.blinded:
                        procs_to_draw.remove("data_obs")
                    plot.subplot(1).Draw(procs_to_draw)

                plot.subplot(0).remove_lower_x_ticks()
                plot.subplot(1)._pad.SetTickx(0)
                plot.add_line(0, 30, split_dict[channel], 6000, split_dict[channel], linestyle=1, color=ROOT.kGray+2)
                for line in plot._lines:
                    line.Draw()
                label2 = ROOT.TLatex()
                label2.SetNDC()
                label2.SetTextAngle(270)
                label2.SetTextColor(ROOT.kGray+2)
                label2.SetTextSize(0.030)
                label2.DrawLatex(0.97, 0.49, "log scale")
                label2.DrawLatex(0.97, 0.70, "linear scale")
                # Redraw upper x axis to have good looking plot
                plot.subplot(0)._pad.cd()
                y_max = max_scale * plot.subplot(0).get_hist("data_obs").GetMaximum()
                axis = ROOT.TGaxis(30., y_max, 5000., y_max, 30., 5000., 510, "GBSU-")
                axis.SetTickLength(0.02)
                axis.SetTickSize(0.02)
                axis.Draw()

            plot.subplot(2).setGrid()

            # Draw upper panel after lower panel of split to ensure full
            # display of the data points
            if args.up_variation is not None:
                procs_to_draw = ["bkg_ggH", "total_bkg_up", "total_bkg_down", "total_bkg", "data_obs"]
            else:
                procs_to_draw = ["bkg_ggH", "total_bkg", "data_obs"]
            if args.blinded:
                procs_to_draw.remove("data_obs")
            plot.subplot(2).Draw(procs_to_draw)

            # create legends
            if int(category) < 30 and int(category) > 2:
                plot.add_legend(width=0.38, height=0.30)
            else:
                # plot.add_legend(width=0.60, height=0.20, pos=1)
                if args.lowmass:
                    plot.add_legend(width=0.25, height=0.42, pos=3)
                else:
                    plot.add_legend(width=0.42, height=0.35, pos=3)
            # plot.add_legend(width=0.6, height=0.15)
            for process in legend_bkg_processes:
                if process == "HSM" and channel == "em":
                    plot.legend(0).add_entry(
                        0, process, "H(125 GeV)", "f")
                else:
                    plot.legend(0).add_entry(
                        0, process, styles.legend_label_dict[process.replace("TTL", "TT").replace("VVL", "VV")], 'f')
            if not args.blinded:
                plot.legend(0).add_entry(0, "data_obs", "Observed", 'PE')
            plot.legend(0).add_entry(0, "total_bkg", "Bkg. unc.", 'f')
            if int(category) > 30:
                mass = 100 if args.lowmass else 1200
                xs = 5.8 if args.lowmass else 0.0031
                mass_str = "%s GeV" % mass if float(mass) < 1000 else "{:.1f} TeV".format(float(mass) / 1000)
                ggH_xs_str = "%s pb" % xs if float(xs) > 1e-2 else "{} fb".format(float(xs) * 1000)
                plot.legend(0).add_entry(0 if args.linear else 1, "", "", '')
                plot.legend(0).add_entry(0 if args.linear else 1, "ggH", "#splitline{gg#phi @ %s}{(m_{#lower[-0.4]{#phi}} = %s)}" % (ggH_xs_str, mass_str), 'l')
            plot.legend(0).setNColumns(1)
            plot.legend(0).scaleTextSize(1.2)
            if not args.lowmass:
                plot.legend(0).setNColumns(2)
                plot.legend(0)._legend.SetMargin(0.35)
            plot.legend(0).Draw()


            # FIXME: Legend for ratio plot temporarily disabled.
            plot.add_legend(
                reference_subplot=2, pos=2, width=0.80, height=0.04)
            if not args.blinded:
                plot.legend(1).add_entry(0, "data_obs", "Observed", 'PE')
            plot.legend(1).add_entry(0, "total_bkg", "Bkg. unc.", 'f')
            if args.up_variation is not None:
                plot.legend(1).add_entry(2, "total_bkg_up", "Up variation", "l")
                plot.legend(1).add_entry(2, "total_bkg_down", "Down variation", "l")
            plot.legend(1).setNColumns(4)
            plot.legend(1).scaleTextSize(1.2)
            plot.legend(1).Draw()

            # draw additional labels
            plot.DrawCMS(cms_sub="Preliminary")
            if "2016" in args.era:
                plot.DrawLumi("36.3 fb^{-1} (2016, 13 TeV)")
            elif "2017" in args.era:
                plot.DrawLumi("41.5 fb^{-1} (2017, 13 TeV)")
            elif "2018" in args.era:
                plot.DrawLumi("59.7 fb^{-1} (2018, 13 TeV)")
            elif "combined" in args.era:
                plot.DrawLumi("138 fb^{-1} (13 TeV)")
            else:
                logger.critical("Era {} is not implemented.".format(args.era))
                raise Exception

            posChannelCategoryLabelLeft = None
            plot.DrawChannelCategoryLabel(
                "%s" % (channel_dict[channel]),
                begin_left=posChannelCategoryLabelLeft)
            plot.DrawText(0.17, 0.82, "#font[42]{"+category_dict[channel][category]+"}", textsize=0.035)
            if args.name is not None:
                plot.DrawText(0.17, 0.78, "#font[42]{"+name_dict[args.name]+"}", textsize=0.035)

            # save plot
            if not os.path.exists(args.output_dir):
                os.makedirs(args.output_dir)
            postfix = "prefit" if "prefit" in args.input else "postfit" if "postfit" in args.input else "undefined"
            plot.save("%s/%s_%s_%s_%s.%s" % (args.output_dir, args.era, channel, args.control_variable if args.control_variable is not None else category,
                                                postfix, "png"
                                                if args.png else "pdf"))
            # Undo switch of split value
            if int(category) < 35 and int(category) > 10:
                split_dict[channel] -= 100
            plots.append(
                plot
            )  # work around to have clean up seg faults only at the end of the script


if __name__ == "__main__":
    args = parse_arguments()
    setup_logging("{}_plot_shapes.log".format(args.era), logging.INFO)
    main(args)
