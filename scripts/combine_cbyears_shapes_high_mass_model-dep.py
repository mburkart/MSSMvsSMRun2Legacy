#!/usr/bin/env python
import os

import ROOT
import array

import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dir",
                        type=str,
                        help="Input directory")
    parser.add_argument('--bOnly', help= 'Use b-only fit result', action='store_true')
    return parser.parse_args()


def restore_binning(src, reference):
    """Implentation taken from CombineHarvester"""
    output = reference.Clone()
    output.Reset()
    output.SetName(src.GetName())
    print("Binning of src histogram: ", [src.GetBinLowEdge(i) for i in range(1, src.GetXaxis().GetNbins()+1)])
    print("Binning of reference histogram: ", [reference.GetBinLowEdge(i) for i in range(1, reference.GetXaxis().GetNbins()+1)])
    for i in range(1, output.GetNbinsX()+1):
        output.SetBinContent(i, src.GetBinContent(i))
        output.SetBinError(i, src.GetBinError(i))
    print("Binning of output histogram: ", [output.GetBinLowEdge(i) for i in range(1, output.GetXaxis().GetNbins()+1)])
    return output


def main(args):
    os.chdir(args.input_dir)

    if args.bOnly:
        fout = ROOT.TFile('shapes_cbyears_bOnly.root','RECREATE')
    else:
        fout = ROOT.TFile('shapes_cbyears.root','RECREATE')

    cb_procs = ['TotalBkg', 'TotalProcs', 'TotalSig', 'data_obs']

    procs = {}
    procs['lt'] = ['EMB','TTL','VVL','ZL','bbA','bbH','ggH_t','ggH_b','ggH_i','ggA_t','ggA_b','ggA_i','jetFakes']
    procs['em'] = ['EMB','QCD','TTL','VVL','W','WHWW125','ZHWW125','ZL','bbH','bbA','ggH_t','ggH_b','ggH_i','ggHWW125','ggA_t','ggA_b','ggA_i','qqHWW125']
    procs['tt'] = ['EMB','TTL','VVL','ZL','bbH','bbA','ggH_t','ggH_b','ggH_i','ggA_t','ggA_b','ggA_i','jetFakes','wFakes']

    dir_map = {
      'tt_32' : 'tt_Nbtag0',
      'tt_35' : 'tt_NbtagGt1',
      'mt_32' : 'mt_Nbtag0_MTLt40',
      'mt_33' : 'mt_Nbtag0_MT40To70',
      'mt_35' : 'mt_NbtagGt1_MTLt40',
      'mt_36' : 'mt_NbtagGt1_MT40To70',
      'et_32' : 'et_Nbtag0_MTLt40',
      'et_33' : 'et_Nbtag0_MT40To70',
      'et_35' : 'et_NbtagGt1_MTLt40',
      'et_36' : 'et_NbtagGt1_MT40To70',
      'em_32' : 'em_Nbtag0_DZetaGt30',
      'em_33' : 'em_Nbtag0_DZetam10To30',
      'em_34' : 'em_Nbtag0_DZetam35Tom10',
      'em_35' : 'em_NbtagGt1_DZetaGt30',
      'em_36' : 'em_NbtagGt1_DZetam10To30',
      'em_37' : 'em_NbtagGt1_DZetam35Tom10',
    }


    for c in ['lt','tt','em']:
        bins = ['32_mt_tot','35_mt_tot']
        if c in ['lt','em']:
            bins.extend(['33_mt_tot','36_mt_tot'])
        if c in ['em']:
            bins.extend(['34_mt_tot','37_mt_tot'])
        for b in bins:
            out_dir = 'htt_%(c)s_%(b)s_postfit' % vars()
            fout.mkdir(out_dir)

            if args.bOnly:
                fin = ROOT.TFile('shapes_cbyears_bOnly_%(c)s_%(b)s.root' % vars())
            else:
                fin = ROOT.TFile('shapes_cbyears_%(c)s_%(b)s.root' % vars())

            print fin, 'shapes_cbyears_bOnly_%(c)s_%(b)s.root' % vars()

            # Get histogram of data_obs from single category for rebinning
            in_ref = ROOT.TFile("restore_binning_combined/common/htt_{c}_{b}_2018_input.root".format(c=c if "lt" not in c else "mt", b=b.replace("_mt_tot", "")), "read")
            ref_hist = in_ref.Get("htt_{c}_{b}_2018/data_obs".format(c=c if "lt" not in c else "mt", b=b.replace("_mt_tot", "")))
            ref_hist.SetDirectory(0)
            in_ref.Close()

            if c == 'lt':
                chans = ['mt','et']
            else:
                chans = [c]

            # get totals first
            for x in cb_procs:
              h = fin.Get('postfit/%(x)s' % vars())
              fout.cd(out_dir)
              h = restore_binning(h, ref_hist)
              h.Write()

            # loop over each process, hadd histograms for different years / channels then write the total to the file
            for x in procs[c]:
                h = fin.Get('postfit/data_obs').Clone()
                h.Reset()
                h.SetName(x)
                for y in [2016, 2017, 2018]:
                    for chan in chans:
                        if isinstance(b,str) and 'mt_tot' in str(b):
                            b_=b.replace('_mt_tot','')
                        else:
                            b_ = b
                        indir = 'htt_%(chan)s_%(b_)s_%(y)s_postfit' % vars()
                        htemp = fin.Get('%(indir)s/%(x)s' % vars())
                        if chan =='em' and 'mt_tot' not in str(b):
                            b_ = b + 1
                            indir2 = 'htt_%(chan)s_%(b_)s_%(y)s_postfit' % vars()
                            htemp2 = fin.Get('%(indir2)s/%(x)s' % vars())
                            if isinstance(htemp2,ROOT.TH1D) or isinstance(htemp2,ROOT.TH1F):
                                htemp.Add(htemp2)
                        if isinstance(htemp,ROOT.TH1D) or isinstance(htemp,ROOT.TH1F):
                            h.Add(htemp)

                fout.cd(out_dir)
                h = restore_binning(h, ref_hist)
                h.Write()


if __name__ == "__main__":
    args = parse_args()
    main(args)
