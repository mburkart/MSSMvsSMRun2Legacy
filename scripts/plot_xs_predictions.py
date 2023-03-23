#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt

import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True


def make_plot(x_vals, y_vals, y_labels,
              log_scale=False, low_tanb=False):
    fig, ax = plt.subplots()
    for y, label in zip(y_vals, y_labels):
        ax.plot(x_vals, y, label=label)

    ax.axvspan(0, 6., facecolor="k", alpha=0.1)

    ax.set_xlabel(r"$\tan\beta$")
    ax.set_ylabel(r"$\sigma(\mathrm{xx}\phi) \cdot \mathrm{BR}(\mathrm{xx}\phi)$ (fb)")

    if low_tanb:
        if log_scale:
            # Zoom with logarithmic y scale
            ax.legend(loc="lower right")

            ax.text(0.05, 0.9, r"$\mathrm{M}_{\mathrm{h}}^{125}$ scenario",
                    transform=ax.transAxes)
            ax.text(0.05, 0.85, r"$\mathrm{m}_{\mathrm{A}} = 1.2$ TeV",
                    transform=ax.transAxes)

            ax.set_yscale("log")
            ax.set_xlim(1, 20)
            fig.savefig("mssm_scan_cross_sections_low-tanb_log.png")
            fig.savefig("mssm_scan_cross_sections_low-tanb_log.pdf")
        else:
            # Zoom in region with low tanb
            ax.legend(loc="upper left")
            ax.set_xlim(1, 20)
            ax.set_ylim(0, 1.1*y_vals[0][19])
            ax.text(0.4, 0.9, r"$\mathrm{M}_{\mathrm{h}}^{125}$ scenario",
                    transform=ax.transAxes)
            ax.text(0.4, 0.85, r"$\mathrm{m}_{\mathrm{A}} = 1.2$ TeV",
                    transform=ax.transAxes)
            fig.savefig("mssm_scan_cross_sections_low-tanb.png")
            fig.savefig("mssm_scan_cross_sections_low-tanb.pdf")
    else:
        ax.legend(loc="upper left")

        ax.text(25, 16, r"$\mathrm{M}_{\mathrm{h}}^{125}$ scenario")
        ax.text(25, 15.2, r"$\mathrm{m}_{\mathrm{A}} = 1.2$ TeV")

        ax.set_xlim(x_vals[0], x_vals[-1])
        ax.set_ylim(0, None)

        fig.savefig("mssm_scan_cross_sections.png")
        fig.savefig("mssm_scan_cross_sections.pdf")
    return


def make_comparison_plot(x_vals, ggPhi_scales, bbPhi_scales):
    fig, ax = plt.subplots()

    ax.plot(x_vals, ggPhi_scales/bbPhi_scales)

    ax.axvspan(0, 6., facecolor="k", alpha=0.1)

    ax.set_xlabel(r"$\tan\beta$")
    ax.set_ylabel(r"$\sigma(\mathrm{gg}\phi) \cdot \mathrm{BR}(\mathrm{gg}\phi) / \sigma(\mathrm{bb}\phi) \cdot \mathrm{BR}(\mathrm{bb}\phi)$")

    # ax.legend(loc="upper left")

    ax.text(0.05, 0.9, r"$\mathrm{M}_{\mathrm{h}}^{125}$ scenario",
            transform=ax.transAxes)
    ax.text(0.05, 0.85, r"$\mathrm{m}_{\mathrm{A}} = 1.2$ TeV",
            transform=ax.transAxes)

    ax.set_xlim(x_vals[0], x_vals[-1])

    ax.set_yscale("log")

    fig.savefig("mssm_scan_cross_section_comparison.png")
    fig.savefig("mssm_scan_cross_section_comparison.pdf")
    return


def main():
    plt.style.use("modtdr")
    # Open root file with workspace and retrieve it.
    infile = ROOT.TFile("analysis_2022_02_28/model-dep_full_with-sm-ml_hSM-in-bg_2022_04_29_mh125/datacards_bsm-model-dep-full/combined/cmb/ws_mh125.root")
    ws = infile.Get("w")

    # Define tanb values to scan.
    tanbs = np.arange(1., 60., 1.)
    # Set mass value
    ws.var("mA").setVal(1200.)

    x = ws.var("x").getVal()
    r = ws.var("r").getVal()
    print(x, r)
    if x != 1. or r != 1.:
        print("[WARNING] Scaling parameters r or x not at 1.")
        print("Values are r = {}, x = {}".format(r, x))

    ggH_scalings = []
    bbH_scalings = []
    ggA_scalings = []
    bbA_scalings = []
    combined = []
    for tanb in tanbs:
        ws.var("tanb").setVal(tanb)
        ggH = sum(ws.function("scaling_ggH_{}".format(c)).getVal()*1000. for c in ["t", "b", "i"])
        ggH_scalings.append(ggH)
        bbH_scalings.append(ws.function("scaling_bbH").getVal()*1000.)
        ggA = sum(ws.function("scaling_ggA_{}".format(c)).getVal()*1000. for c in ["t", "b", "i"])
        ggA_scalings.append(ggA)
        bbA_scalings.append(ws.function("scaling_bbA").getVal()*1000.)
        combined.append(sum((ggH_scalings[-1], ggA_scalings[-1], bbH_scalings[-1], bbA_scalings[-1])))

    # convert lists to numpy arrays
    comb = np.array(combined)
    ggH_scale = np.array(ggH_scalings)
    ggA_scale = np.array(ggA_scalings)
    bbH_scale = np.array(bbH_scalings)
    bbA_scale = np.array(bbA_scalings)
    print(bbH_scale[tanbs==17.])
    print(bbA_scale[tanbs==17.])
    print(ggH_scale[tanbs==17.])
    print(ggA_scale[tanbs==17.])
    bb_frac = (bbH_scale + bbA_scale)/comb
    gg_frac = (ggH_scale + ggA_scale)/comb
    print(bb_frac[np.all([tanbs>11.5, tanbs<20.5], axis=0)])
    print(gg_frac[np.all([tanbs>11.5, tanbs<20.5], axis=0)])

    infile.Close()

    make_plot(tanbs, [combined, ggH_scalings, ggA_scalings, bbH_scalings, bbA_scalings],
              ["xxH + xxA", "ggH", "ggA", "bbH", "bbA"])
    make_plot(tanbs, [combined, ggH_scalings, ggA_scalings, bbH_scalings, bbA_scalings],
              ["xxH + xxA", "ggH", "ggA", "bbH", "bbA"],
              low_tanb=True)
    make_plot(tanbs, [combined, ggH_scalings, ggA_scalings, bbH_scalings, bbA_scalings],
              ["xxH + xxA", "ggH", "ggA", "bbH", "bbA"],
              low_tanb=True, log_scale=True)
    make_comparison_plot(tanbs, ggH_scale + ggA_scale, bbH_scale + bbA_scale)
    return


if __name__ == "__main__":
    main()
