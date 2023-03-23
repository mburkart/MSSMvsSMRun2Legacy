#!/usr/bin/env python

from array import array
import yaml

import ROOT

channel_cats = {
        "et": ["32", "33", "35", "36"],
        "mt": ["32", "33", "35", "36"],
        "tt": ["32", "35"],
        "em": map(str, range(32,38))
}

category_dict = {
    "et": {
        "32": "e#tau_{h} no b-tag tight-m_{T}",
        "33": "e#tau_{h} no b-tag loose-m_{T}",
        "35": "e#tau_{h} b-tag tight-m_{T}",
        "36": "e#tau_{h} b-tag loose-m_{T}",
    },
    "mt": {
        "32": "#mu#tau_{h} no b-tag tight-m_{T}",
        "33": "#mu#tau_{h} no b-tag loose-m_{T}",
        "35": "#mu#tau_{h} b-tag tight-m_{T}",
        "36": "#mu#tau_{h} b-tag loose-m_{T}",
    },
    "tt": {
        "32": "#tau_{h}#tau_{h} no b-tag",
        "35": "#tau_{h}#tau_{h} b-tag",
    },
    "em": {
        "32": "e#mu no b-tag high-d_{#zeta}",
        "33": "e#mu no b-tag medium-d_{#zeta}",
        "34": "e#mu no b-tag low-d_{#zeta}",
        "35": "e#mu b-tag high-d_{#zeta}",
        "36": "e#mu b-tag medium-d_{#zeta}",
        "37": "e#mu b-tag low-d_{#zeta}",
    },
}

legend_label = {
    "HTT": 'H#rightarrow#tau#tau',
    "ggH": 'gg#rightarrowH',
    "qqH": 'qq#rightarrowH',
    "VH": 'qq#rightarrowVH',
    "WH": 'qq#rightarrowWH',
    "ZH": 'qq#rightarrowZH',
    "ZTT": 'Z#rightarrow#tau#tau',
    "EMB": '#splitline{#mu#rightarrow#tau}{embedded}',
    "ZLL": 'Z#rightarrowll',
    "ZL": 'Z#rightarrowll',
    "ZJ": 'Z#rightarrowll (jet#rightarrow^{}#tau_{h})',
    "TT": 't#bar{t}',
    "TTT": 't#bar{t} (#tau#tau)',
    "TTL": 't#bar{t} (l#tau)',
    "TTJ": 't#bar{t} (jet#rightarrow^{}#tau_{h})',
    "W": 'W+jets',
    "WT": '(W#rightarrow#tau)+jets',
    "WL": '(W#slash{#rightarrow}#tau)+jets',
    "VV": 'Diboson',
    "VVT": 'Diboson (#tau#tau)',
    "VVJ": 'Diboson (jet#rightarrow^{}#tau_{h})',
    "VVL": '#splitline{Diboson}{(l#tau)}',
    "ST": 'Single t',
    "STT": 'Single t',
    "STL": 'Single t',
    "QCD": 'QCD multijet',
    "QCDEMB": 'QCD multijet',
    "EWK": 'Electroweak',
    "EWKT": 'Electroweak (t#rightarrow^{}#tau_{h})',
    "EWKL": 'Electroweak (l#rightarrow^{}#tau_{h})',
    "EWKJ": 'Electroweak (jet#rightarrow^{}#tau_{h})',
    "EWKZ": 'EWKZ',
    "jetFakes": 'Jet#rightarrow^{}#tau_{h}',
    "jetFakesW": 'Jet#rightarrow^{}#tau_{h} (W)',
    "jetFakesQCD": 'Jet#rightarrow^{}#tau_{h} (QCD)',
    "jetFakesTT": 'Jet#rightarrow^{}#tau_{h} (TT)',
    "jetFakesEMB": 'Jet#rightarrow^{}#tau_{h}',
    "data_obs": 'Data',
}

color_dict = {
    "ggH": ROOT.TColor.GetColor("#BF2229"),
    "qqH": ROOT.TColor.GetColor("#00A88F"),
    "VH": ROOT.TColor.GetColor("#001EFF"),
    "WH": ROOT.TColor.GetColor("#001EFF"),
    "ZH": ROOT.TColor.GetColor("#001EFF"),
    "ttH": ROOT.TColor.GetColor("#FF00FF"),
    "bbH": ROOT.TColor.GetColor("#009900"),
    "HWW": ROOT.TColor.GetColor("#FF8C00"),
    "ZTT": ROOT.TColor.GetColor(248, 206, 104),
    "EMB": ROOT.TColor.GetColor(248, 206, 104),
    "ZLL": ROOT.TColor.GetColor(100, 192, 232),
    "ZL": ROOT.TColor.GetColor(100, 192, 232),
    "ZJ": ROOT.TColor.GetColor("#64DE6A"),
    "TT": ROOT.TColor.GetColor(155, 152, 204),
    "TTT": ROOT.TColor.GetColor(155, 152, 204),
    "TTL": ROOT.TColor.GetColor(155, 152, 204),
    "TTJ": ROOT.TColor.GetColor(215, 130, 204),
    "W": ROOT.TColor.GetColor(222, 90, 106),
    "WT": ROOT.TColor.GetColor(222, 90, 106),
    "WL": ROOT.TColor.GetColor(222, 150, 80),
    "VV": ROOT.TColor.GetColor("#6F2D35"),
    "VVT": ROOT.TColor.GetColor("#6F2D35"),
    "VVJ": ROOT.TColor.GetColor("#c38a91"),
    "VVL" : ROOT.TColor.GetColor("#6F2D35"),
    "ST": ROOT.TColor.GetColor("#d0f0c1"),
    "STT": ROOT.TColor.GetColor("#d0f0c1"),
    "STL" : ROOT.TColor.GetColor("#d0f0c1"),
    "QCD": ROOT.TColor.GetColor(250, 202, 255),
    "QCDEMB": ROOT.TColor.GetColor(250, 202, 255),
    "QCDMC": ROOT.TColor.GetColor(250, 202, 255),
    "EWK": ROOT.TColor.GetColor("#E1F5A9"),
    "EWKT": ROOT.TColor.GetColor("#E1F5A9"),
    "EWKL": ROOT.TColor.GetColor("#E1F5A9"),
    "EWKJ": ROOT.TColor.GetColor("#E1F5A9"),
    "EWKZ": ROOT.TColor.GetColor("#E1F5A9"),
    "jetFakes": ROOT.TColor.GetColor(192, 232, 100),
    "jetFakesW": ROOT.TColor.GetColor(222, 90, 106),
    "jetFakesQCD": ROOT.TColor.GetColor(250, 202, 255),
    "jetFakesTT": ROOT.TColor.GetColor(155, 152, 204),
    "jetFakesEMB": ROOT.TColor.GetColor(192, 232, 100),
    "jetFakesMC": ROOT.TColor.GetColor(192, 232, 100),
}


def extract_yields(era, channel, cat):
    infile = ROOT.TFile("analysis_2022_02_28/model-indep_classic_hSM-in-bg/datacards_bsm-model-indep/combined/cmb/prefit_shapes_MH=1200,r_ggH=0.0031,r_bbH=0.0031.root", "read")
    proc_yields = {}
    if channel in ["et", "mt"]:
        procs_to_extract = ["jetFakes", "EMB", "ZL", "TTL", "VVL", "HSM", "TotalBkg"]
    elif channel in ["tt"]:
        procs_to_extract = ["jetFakes", "wFakes", "EMB", "ZL", "TTL", "VVL", "HSM", "TotalBkg"]
    elif channel in ["em"]:
        procs_to_extract = ["EMB", "QCD", "ZL", "TTL", "VVL", "W", "HSM", "HWW", "TotalBkg"]

    for proc in procs_to_extract:
        # print("Querying {}".format("htt_{}_{}_{}_prefit/{}".format(channel,
        #                                         cat,
        #                                         era,
        #                                         proc)))
        try:
            if proc == "HSM":
                proc_yields[proc] = infile.Get(
                        "htt_{}_{}_{}_prefit/{}".format(channel,
                                                        cat,
                                                        era,
                                                        "ggH125")).Integral()
                proc_yields[proc] += infile.Get(
                        "htt_{}_{}_{}_prefit/{}".format(channel,
                                                        cat,
                                                        era,
                                                        "qqH125")).Integral()
            elif proc == "HWW":
                proc_yields[proc] = infile.Get(
                        "htt_{}_{}_{}_prefit/{}".format(channel,
                                                        cat,
                                                        era,
                                                        "ggHWW125")).Integral()
                proc_yields[proc] += infile.Get(
                        "htt_{}_{}_{}_prefit/{}".format(channel,
                                                        cat,
                                                        era,
                                                        "qqHWW125")).Integral()
                proc_yields[proc] += infile.Get(
                        "htt_{}_{}_{}_prefit/{}".format(channel,
                                                        cat,
                                                        era,
                                                        "WHWW125")).Integral()
                proc_yields[proc] += infile.Get(
                        "htt_{}_{}_{}_prefit/{}".format(channel,
                                                        cat,
                                                        era,
                                                        "ZHWW125")).Integral()
            else:
                proc_yields[proc] = infile.Get(
                        "htt_{}_{}_{}_prefit/{}".format(channel,
                                                        cat,
                                                        era,
                                                        proc)).Integral()
        except AttributeError as err:
            print(err)
            print("Tried to extract htt_{}_{}_{}_prefit/{}".format(channel,
                                                cat,
                                                era,
                                                proc))
            proc_yields[proc] = 0.
    return proc_yields


def calculate_fraction(proc):
    if proc == "jetFakesFull":
        return (process_dict[category]["jetFakes"] + process_dict[category]["wFakes"])/process_dict[category]["TotalBkg"]
    else:
        return process_dict[category][x]/process_dict[category]["TotalBkg"]


def print_fraction(process_dict, channel, category):
    if channel in ["et", "mt"]:
        procs_to_extract = ["jetFakes", "EMB"]
    elif channel in ["tt"]:
        procs_to_extract = ["jetFakes", "wFakes", "jetFakesFull", "EMB"]
    elif channel in ["em"]:
        procs_to_extract = ["EMB"]
    print("\t".join(procs_to_extract))
    print("\t".join(map(str, map(lambda x: process_dict[category][x]/process_dict[category]["TotalBkg"] if x != "jetFakesFull" else (process_dict[category]["jetFakes"] + process_dict[category]["wFakes"])/process_dict[category]["TotalBkg"], procs_to_extract))))


def main():
    proc_dict = {}
    for ch in ["et", "mt", "tt", "em"]:
        proc_dict[ch] = {}
        for era in ["2016", "2017", "2018"]:
            proc_dict[ch][era] = {}
            for cat in channel_cats[ch]:
                proc_dict[ch][era][cat] = extract_yields(era, ch, cat)

            proc_dict[ch][era]["combined"] = {}
            for proc in proc_dict[ch][era]["32"].keys():
                proc_dict[ch][era]["combined"][proc] = 0.
                for cat in channel_cats[ch]:
                    proc_dict[ch][era]["combined"][proc] += proc_dict[ch][era][cat][proc]

            print("Era: {}, Channel: {}".format(era, ch))
            print_fraction(proc_dict[ch][era], ch, "combined")
    # Write out final dict to yaml for further use, e.g. plotting
    with open("event_contents.yaml", "w") as yfi:
        yaml.dump(proc_dict, yfi)
    return


if __name__ == "__main__":
    main()
