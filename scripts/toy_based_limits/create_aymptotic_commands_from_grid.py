#!/usr/bin/env python

import argparse

import ROOT

CMD_TEMPLATE = "if [[ $1 -eq {job} ]]; then\n" \
               "\tcombine -M AsymptoticLimits -m {mass} --rAbsAcc 0 --rRelAcc 0.0005 --setParameters {non_poi}=0 --setParameterRanges r_ggH=0,1:r_bbH=0,1:CMS_htt_ttbarShape=-1,1 --redefineSignalPOIs {poi} -d /work/mburkart/Run2Legacy/Run2LegacyFitting_unblinding/CMSSW_10_2_25/src/CombineHarvester/MSSMvsSMRun2Legacy/analysis_v12/cmb_ind/datacards_bsm-model-indep/combined/cmb/ws.root --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 -v1 --singlePoint {point} -n .{poi}.{point}\n" \
               "fi\n"

SETUP = """ \
#!/bin/sh
ulimit -s unlimited
set -e
cd /work/mburkart/Run2Legacy/Run2LegacyFitting_unblinding/CMSSW_10_2_25/src
export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 runtime -sh`
cd /work/mburkart/Run2Legacy/Run2LegacyFitting_unblinding/CMSSW_10_2_25/src/CombineHarvester/MSSMvsSMRun2Legacy/analysis_v12/cmb_ind/limits_ind_toys

"""

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input",
                        type=str,
                        help="Input grid file of hybrid results."
    )
    parser.add_argument("-p", "--poi",
                        choices=["r_ggH", "r_bbH"],
                        type=str,
                        help="Name of the poi to be considered."
    )
    parser.add_argument("-m", "--mass",
                        type=str,
                        help="Mass hypothesis considered in the grid file."
    )
    parser.add_argument("-o", "--output",
                        type=str,
                        help="Output file name"
    )
    return parser.parse_args()


def read_poi_values_from_grid(infile):
    toy_dir = infile.Get("toys")
    # The readout assumes the results are named in the form
    # HypoTestResult_mh3200_r_bbH0.00152838_4161823192
    poi_vals = [key.GetName().replace("H0", "H_0").split("_")[4] for key in toy_dir.GetListOfKeys() if key.GetName().startswith("HypoTestResult_mh")]
    return set(poi_vals)


def main(args):
    infile = ROOT.TFile(args.input, "read")

    poi_vals = read_poi_values_from_grid(infile)
    # Add setup part to generated output file.
    with open(args.output, "w") as fi:
        fi.write(SETUP)
        counter = 0
        for val in poi_vals:
            fi.write(CMD_TEMPLATE.format(job=counter,
                                         mass=args.mass,
                                         non_poi="r_bbH" if args.poi == "r_ggH" else "r_ggH",
                                         poi=args.poi,
                                         point=val))
            counter += 1
    return


if __name__ == "__main__":
    args = parse_args()
    main(args)
