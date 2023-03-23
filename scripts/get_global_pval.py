#!/usr/bin/env python

import os
import argparse
import json

import numpy as np
from scipy.stats import beta, norm

import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True


masses = [60, 80, 100, 120, 125, 130, 140, 160, 180, 200,
          250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000,
          1200, 1400, 1600, 1800, 2000, 2300, 2600, 2900, 3200, 3500]
# masses_red = [250, 300, 350, 400, 450, 500, 600, 700, 800, 900, 1000,
#               1200, 1400, 1600, 1800, 2000, 2300, 2600, 2900, 3200, 3500]
# masses = masses_red


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-i", "--input-dir",
            help="The directory containing datacards and results"
    )
    parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Print more information on results"
    )
    return parser.parse_args()


def estimate_phat(k, n, unc="wald"):
    alpha = 0.68
    phat = k/n
    if unc == "wald":
        p_d = phat - np.sqrt(phat*(1-phat)/n)
        p_u = phat + np.sqrt(phat*(1-phat)/n)
    elif unc == "cp":
        p_d, p_u = beta.ppf([alpha/2., 1-alpha/2.], [k, k+1], [n-k+1, n-k])
    return phat, p_u, p_d


def create_limit_array(indir,
                       sig_dir="global_significance",
                       toy_range=(0,400)):
    # Build a TChain of all inputs for single masses, read limits and build 2d array
    limits = []
    base_path = os.path.join(
            indir,
            # "significance_ind_global",
            sig_dir,
            "condor")
    for mass in masses:
        chain = ROOT.TChain("limit")
        # mrange = range(101, 500)
        mrange = range(*toy_range)
        for i in mrange:
            # chain.Add(os.path.join(base_path,"higgsCombine.ggH.{}.Significance.mH{}.123456.root".format(i, mass)))
            chain.Add(os.path.join(base_path,
                                   "higgsCombine.ggH.{i}.Significance.mH{m}.{i}.root".format(i=i, m=mass)))
        if chain.GetEntries() != len(mrange)*20:
            raise ValueError("Number of toys does not match expected for mass {}".format(mass))
        limits.append(ROOT.RDataFrame(chain).AsNumpy(columns=["limit"])["limit"])
    return np.array(limits)


def main(args):
    # Read input root file containing all significances for toys
    limits = create_limit_array(args.input_dir)
    # limits = create_limit_array("analysis_2022_02_28/model-indep_classic_2022-04-21_hSM-in-bg")
    # print(limits.ndim)
    limits_max = np.max(limits, axis=0)
    ind = np.argmax(limits, axis=0)
    if args.verbose:
        print("Distribution of maxima across mass indices:")
        print(np.unique(ind, return_counts=True))
        print("Maximal significance per toy:")
        print(limits_max)
    for mass in [130, 1200]:
        # Read significance of mass point at 130 GeV
        # inname = os.path.join(
        #         args.input_dir,
        #         "datacards_bsm-model-indep",
        #         "combined",
        #         "cmb",
        #         "higgsCombine.ggH.Significance.mH{}.root".format(mass))
        inname = os.path.join(
                args.input_dir,
                "significance_ind",
                "condor",
                "higgsCombine.ggH.Significance.mH{}.root".format(mass))

        infile = ROOT.TFile(inname, "read")
        intree = infile.Get("limit")
        if intree.GetEntries() > 1:
            raise ValueError("Input tree for significance should only have one entry")
        intree.GetEntry(0)
        sig = intree.limit
        local_p = ROOT.RooStats.SignificanceToPValue(sig)
        print(f"Printing results for excess at the mass m = {mass} GeV")
        print(f"Local significance: {sig}")
        print(f"Local p-value: {local_p}")
        # limits_max = limits_max[limits_max<10.]
        phat = estimate_phat(float(limits_max[limits_max>sig].size),
                             float(limits_max.size))
        print(f"p-value for m = {mass} GeV: {phat}")
        significances = norm.isf(phat)
        significances[1:] -= significances[0]
        print(f"Significances: {significances}")
        if args.verbose:
            print("Results of different methods of signficance calculation:")
            print(ROOT.RooStats.PValueToSignificance(phat[0]))
            print(ROOT.Math.normal_quantile_c(phat[0],1))
            print("p-value when adding local and global p-value")
            print(ROOT.RooStats.PValueToSignificance(phat[0]+local_p))

        # Write out json in the style of GoF results
        # out = {"{:.1f}".format(mass): {}}
        out = {}
        out["obs"] = [sig]
        out["p"] = phat[0]
        # Uncertainty calculation assumes Wald intervals, which are symmetric
        out["p_unc"] = phat[1] - phat[0]
        out["toys"] = list(limits_max)
        outfile = os.path.join(
                args.input_dir,
                "global_significance",
                "global_p-value_mH{}.json".format(mass)
                )
        with open(outfile, "w") as fi:
            json.dump({"{:.1f}".format(mass): out}, fi,
                      indent=4)
        if args.verbose:
            # Write out the same for the local p-value
            out = {}
            out["obs"] = [sig]
            out["p"] = local_p
            if mass == 130:
                out["toys"] = list(limits[5,:])
            else:
                out["toys"] = list(limits[21,:])
            outfile = os.path.join(
                    args.input_dir,
                    "global_significance",
                    "local_p-value_mH{}.json".format(mass)
                    )
            with open(outfile, "w") as fi:
                json.dump({"{:.1f}".format(mass): out}, fi,
                          indent=4)
            # Write out the result for a single toy
            if mass == 1200:
                continue
            out = {}
            indices = np.nonzero(limits_max>3.5)[0]
            for index in indices:
                for tmass, tsig in zip(masses, list(limits[:,index])):
                    out[f"{tmass:.1f}"] = {"obs": tsig}
                outfile = os.path.join(
                        args.input_dir,
                        "global_significance",
                        f"toy_p-value_mH{mass}_{index}.json"
                        )
                with open(outfile, "w") as fi:
                    json.dump(out, fi,
                              indent=2, sort_keys=True)
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
