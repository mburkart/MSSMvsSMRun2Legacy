#!/usr/bin/env python
import glob
import sys
import os
from multiprocessing import Pool
import argparse
from array import array

import numpy as np

import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-path",
                        type=str,
                        help="Directory with root files from the toys"
    )
    parser.add_argument("-r", "--signal-strength",
                        type=str,
                        help="Signal strength the test statistic is computed for"
    )
    parser.add_argument("-m", "--mass",
                        type=str,
                        default="2900",
                        help="Mass of the signal hypothesis"
    )
    parser.add_argument("-p", "--process",
                        type=str,
                        default="r_ggH",
                        help="Mass of the signal hypothesis"
    )
    return parser.parse_args()


def main(args):
    chosen_files = glob.glob(os.path.join(args.input_path, "higgsCombine.MH.{mH}.0.{proc}.{r_ggH}.HybridNew.mH{mH}.*.root".format(mH=args.mass, r_ggH=args.signal_strength, proc=args.process)))
    print("# files:",len(chosen_files))

    background_toys = []
    signal_toys = []

    c = ROOT.TCanvas()
    c.cd()

    for f in chosen_files:
        F = ROOT.TFile.Open(f, "read")
        d = F.Get("toys")
        if len([k for k in d.GetListOfKeys()]) == 0:
            F.Close()
            continue
        for key in d.GetListOfKeys():
            if key.GetName().startswith("HypoTestResult"):
                hypotest_name = key.GetName()
                break
        hypotest = d.Get(hypotest_name)
        background_toys += list(hypotest.GetNullDistribution().GetSamplingDistribution())
        signal_toys += list(hypotest.GetAltDistribution().GetSamplingDistribution())
        F.Close()

    print("Number of toys for {p} at {m} GeV and {r}:".format(p=args.process, m=args.mass, r=args.signal_strength))
    print("# BG toys:",len(background_toys))
    print("# S toys:",len(signal_toys))
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
