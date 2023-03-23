#!/usr/bin/env python

import argparse
import os
from array import array

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

import Dumbledraw.dumbledraw as dd
import Dumbledraw.rootfile_parser as rootfile_parser
import Dumbledraw.styles as styles

scen_name = {
    "mh125": "M_{h}^{125} scenario",
    "mh125EFT": "M_{h, #kern[0.16667]{E}FT}^{125} scenario",
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--boson",
                        type=str,
                        choices=["h", "H", "A"],
                        required=True,
                        help="The considered Higgs boson for the pT reweighting")
    parser.add_argument("-s", "--scenario",
                        type=str,
                        help="MSSM benchmark scenario used to extract the cross sections")
    parser.add_argument("-m", "--mA",
                        type=float,
                        help="mA value where cross sections are evaluated")
    parser.add_argument("-t", "--tanb",
                        type=float,
                        help="tanb value where cross sections are evaluated")
    parser.add_argument("--no-normalization",
                        action="store_true",
                        help="Do not normalize the histograms by bin width.")
    parser.add_argument("-r", "--reference-tanb",
                        type=float,
                        default=None,
                        help="Reference parameter point given by mA and tanb for denominator")
    return parser.parse_args()


def get_hist_copy(hist):
    nxbins = hist.GetXaxis().GetNbins()
    x_bins = [hist.GetBinLowEdge(i) for i in range(1,nxbins+2)]
    hc = ROOT.TH1D(hist.GetName()+"_copy", hist.GetTitle(), nxbins, array("d", x_bins))
    for i in range(1, nxbins+1):
        hc.SetBinContent(i, hist.GetBinContent(i))
    return hc


def main(args):
    # Plot the different histograms
    width=600
    if args.reference_tanb is not None:
        plot = dd.Plot([0.25, [0.25, 0.23]], style="ModTDR", r=0.04, l=0.14, width=width)
    else:
        plot = dd.Plot([0.0], style="ModTDR", r=0.04, l=0.14, width=width)

    ws_filename = "data/higgs_pt_reweighting_fullRun2.root"

    scenario_inputs = "data/{}_13.root".format(args.scenario)

    # Get workspace from input file
    ws_file = ROOT.TFile(ws_filename, "read")
    ws = ws_file.Get("w")
    # And extract histograms and fractions from the workspace
    top_hist = get_hist_copy(ws.genobj("hist_{}_{}_t".format(args.boson, int(args.mA))))
    bot_hist = get_hist_copy(ws.genobj("hist_{}_{}_b".format(args.boson, int(args.mA))))
    int_hist = get_hist_copy(ws.genobj("hist_{}_{}_i".format(args.boson, int(args.mA))))
    top_hist.SetDirectory(0)
    bot_hist.SetDirectory(0)
    int_hist.SetDirectory(0)

    # Extract fractions from workspace and scale to predicted cross section afterwards
    scen_fi = ROOT.TFile(scenario_inputs, "read")
    yt_hist = scen_fi.Get("rescale_gt_{}".format(args.boson))
    yb_hist = scen_fi.Get("rescale_gb_{}".format(args.boson))
    ws.var("Yt_MSSM_{}".format(args.boson)).setVal(yt_hist.GetBinContent(yt_hist.FindBin(args.mA, args.tanb)))
    ws.var("Yb_MSSM_{}".format(args.boson)).setVal(yb_hist.GetBinContent(yb_hist.FindBin(args.mA, args.tanb)))
    ws.var("m{}".format(args.boson)).setVal(args.mA)
    top_frac = ws.function("gg{}_t_MSSM_frac".format(args.boson)).getVal()
    bot_frac = ws.function("gg{}_b_MSSM_frac".format(args.boson)).getVal()
    int_frac = ws.function("gg{}_i_MSSM_frac".format(args.boson)).getVal()

    # Read also cross sections from input file
    nnlo_xsec_hist = scen_fi.Get("xs_gg_{}".format(args.boson))
    nnlo_xsec = nnlo_xsec_hist.GetBinContent(nnlo_xsec_hist.FindBin(args.mA, args.tanb))
    if args.reference_tanb is not None:
        # Get unscaled version of histograms for comparison of density with
        # reference benchmark point
        top_hist_unscaled = top_hist.Clone()
        top_hist_unscaled.Scale(top_frac)
        bot_hist_unscaled = bot_hist.Clone()
        bot_hist_unscaled.Scale(bot_frac)
        int_hist_unscaled = int_hist.Clone()
        int_hist_unscaled.Scale(int_frac)
        # Add them up to form total histogram
        tot_hist_unscaled = top_hist_unscaled.Clone()
        tot_hist_unscaled.Add(bot_hist_unscaled)
        tot_hist_unscaled.Add(int_hist_unscaled)
        # Extract the same histograms also for reference points
        top_hist_ref = top_hist.Clone()
        bot_hist_ref = bot_hist.Clone()
        int_hist_ref = int_hist.Clone()
        # Extract fractions for reference points
        ws.var("Yt_MSSM_{}".format(args.boson)).setVal(yt_hist.GetBinContent(yt_hist.FindBin(args.mA, args.reference_tanb)))
        ws.var("Yb_MSSM_{}".format(args.boson)).setVal(yb_hist.GetBinContent(yb_hist.FindBin(args.mA, args.reference_tanb)))
        top_frac_ref = ws.function("gg{}_t_MSSM_frac".format(args.boson)).getVal()
        bot_frac_ref = ws.function("gg{}_b_MSSM_frac".format(args.boson)).getVal()
        int_frac_ref = ws.function("gg{}_i_MSSM_frac".format(args.boson)).getVal()
        top_hist_ref.Scale(top_frac_ref)
        bot_hist_ref.Scale(bot_frac_ref)
        int_hist_ref.Scale(int_frac_ref)
        tot_hist_ref = top_hist_ref.Clone()
        tot_hist_ref.Add(bot_hist_ref)
        tot_hist_ref.Add(int_hist_ref)
    top_hist.Scale(top_frac*nnlo_xsec)
    bot_hist.Scale(bot_frac*nnlo_xsec)
    int_hist.Scale(int_frac*nnlo_xsec)
    ws_file.Close()

    plot.add_hist(top_hist, "pT_top")
    plot.add_hist(bot_hist, "pT_bot")
    plot.add_hist(int_hist, "pT_int")

    tot_hist = top_hist.Clone()
    tot_hist.Add(bot_hist)
    tot_hist.Add(int_hist)

    plot.add_hist(tot_hist, "pT_tot")
    if args.reference_tanb is not None:
        plot.subplot(2).add_hist(tot_hist_unscaled, "pT_tot_u")
        plot.subplot(2).add_hist(tot_hist_ref, "pT_tot_r")

    plot.setGraphStyle("pT_top", "hist",
                       fillcolor=ROOT.TColor.GetColor("#c2eabd"),
                       linecolor=ROOT.TColor.GetColor("#43ab36"),
                       linewidth=2)
    plot.setGraphStyle("pT_bot", "hist",
                       fillcolor=ROOT.TColor.GetColor("#f9dc5c"),
                       linecolor=ROOT.TColor.GetColor("#ecc209"),
                       linewidth=2)
    plot.setGraphStyle("pT_int", "hist",
                       fillcolor=ROOT.TColor.GetColor("#ed254e"),
                       linecolor=ROOT.TColor.GetColor("#aa0e2d"),
                       linewidth=2)
    plot.setGraphStyle("pT_tot", "hist",
                       linecolor=ROOT.kBlack,
                       linewidth=2)

    plot.create_stack(["pT_int", "pT_bot", "pT_top"], "pT_stack")


    if args.reference_tanb is not None:
        plot.subplot(2).normalize(["pT_tot_u", "pT_tot_r"], "pT_tot_r")
        plot.subplot(2).setGraphStyle("pT_tot_u", "hist",
                                      linecolor=ROOT.kBlack,
                                      linewidth=2)

    if args.no_normalization:
        tmp_hist = plot.subplot(0).get_hist("pT_top").Clone()
        tmp_hist.Add(plot.subplot(0).get_hist("pT_bot"))
        tmp_hist.Add(plot.subplot(0).get_hist("pT_int"))
        # plot.subplot(0).setYlims(0, 1.2*tmp_hist.GetMaximum())
        plot.subplot(0).setYlabel("Events")
    else:
        plot.subplot(0).normalizeByBinWidth()
        tmp_hist = plot.subplot(0).get_hist("pT_top").Clone()
        tmp_hist.Add(plot.subplot(0).get_hist("pT_bot"))
        tmp_hist.Add(plot.subplot(0).get_hist("pT_int"))
        # plot.subplot(0).setYlims(0, 1.2*tmp_hist.GetMaximum())
        plot.subplot(0).setYlabel("dN/p_{{#lower[-0.1]{{T}}}}^{{{h}}} (1/GeV)".format(h=args.boson))

    plot.setXlims(0, 400)
    # Calculate sum of histograms to set y axis limits.
    if args.reference_tanb is not None:
        plot.subplot(2).setGrid()
        plot.subplot(2).setYlims(0.4, 1.6)
        plot.subplot(2).setNYdivisions(3, 2)
        plot.subplot(2).setNXdivisions(5, 6)
        plot.subplot(2).setYlabel("#splitline{Ratio to}{tan#kern[0.16667]{#beta}=15}")
        plot.subplot(2).setXlabel("p_{{#lower[-0.1]{{T}}}}^{{{h}}} (GeV)".format(h=args.boson))
        plot.subplot(2).scaleYTitleOffset(0.85)
    else:
        plot.subplot(0).setXlabel("p_{{T}}^{{{h}}} (GeV)".format(h=args.boson))

    plot.scaleYLabelSize(0.8)
    if int(args.tanb) == 30:
        plot.subplot(0).removeYTickLabels([-1])
        # plot.scaleYTitleOffset(1.1)

    plot.subplot(0).Draw(["pT_stack", "pT_tot"])
    if args.reference_tanb is not None:
        plot.subplot(2).Draw(["pT_tot_u"])
    plot.DrawLumi("Simulation, 13 TeV")

    plot.add_legend(width=0.40, height=0.3)
    plot.legend(0).add_entry(0, "pT_top", "t quark contribution", "f")
    plot.legend(0).add_entry(0, "pT_bot", "b quark contribution", "f")
    plot.legend(0).add_entry(0, "pT_int", "Interference contribution", "f")
    plot.legend(0).scaleTextSize(1.3)
    plot.legend(0).Draw()

    ROOT.TGaxis.SetMaxDigits(4)
    # ROOT.TGaxis.SetExponentOffset(-0.07, 0.02, "Y")

    highest = 0.50
    plot.DrawText(0.67, highest, "M_{h}^{125} scenario", textsize=0.0425)
    if int(args.mA) < 1000:
        plot.DrawText(0.70, highest - 0.05, "#font[42]{{m_{{A}} = {} GeV}}".format(int(args.mA)), textsize=0.0315)
    else:
        plot.DrawText(0.70, highest - 0.05, "#font[42]{{m_{{A}} = {:.1f} TeV}}".format(float(args.mA)/1000.), textsize=0.0315)
    plot.DrawText(0.70, highest - 0.09, "#font[42]{{tan#kern[0.16667]{{#beta}} = {}}}".format(int(args.tanb)), textsize=0.0315)


    outdir = "higgs_pt_distributions"
    outname = "higgs_pt_{scen}_{h}_{mA}_{tanb}.pdf".format(scen=args.scenario, h=args.boson,
                                                           mA=int(args.mA),
                                                           tanb=int(args.tanb))
    if not os.path.exists(outdir):
        os.makedir(outdir)
    plot.save(os.path.join(outdir, outname))
    plot.save(os.path.join(outdir, outname).replace(".pdf", ".png"))
    plot.save(os.path.join(outdir, outname).replace(".pdf", ".C"))
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
