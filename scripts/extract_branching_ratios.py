#/usr/bin/env python

import yaml

from CombineHarvester.MSSMvsSMRun2Legacy.mssm_xs_tools import mssm_xs_tools


def main():
    # Write out branching ratios for multiple particles from
    # mh125 benchmark scenario

    # List of parameters we want to consider:
    # Use a single mass that is not too high
    mA = 600.
    # and too tan b values
    tanbs = [7., 14.]
    # Open the root file
    mssm_inputs = mssm_xs_tools("data/mh125_13.root", False, 1)
    # Set up the list of branching ratios available
    brs = [
        # Decay modes special for A boson
        "A->Zh",
        "A->ZH",
        # Decay modes present for all Higgs bosons
        "A->SUSY",
        "A->WW",
        "A->ZZ",
        "A->Zgam",
        "A->bb",
        "A->cc",
        "A->gamgam",
        "A->gluglu",
        "A->mumu",
        "A->tautau",
        "A->tt",

        # Different decay modes for H boson
        "H->AA",
        "H->hh",
        "H->WHp",
        "H->ZA",
        # Decay modes present for all Higgs bosons
        "H->SUSY",
        "H->WW",
        "H->ZZ",
        "H->Zgam",
        "H->bb",
        "H->cc",
        "H->gamgam",
        "H->gluglu",
        "H->mumu",
        "H->tautau",
        "H->tt",

        "h->SUSY",
        "h->WW",
        "h->ZZ",
        "h->Zgam",
        "h->bb",
        "h->cc",
        "h->gamgam",
        "h->gluglu",
        "h->mumu",
        "h->tautau",
        "h->tt",

        "HSM->WW",
        "HSM->ZZ",
        "HSM->Zgam",
        "HSM->bb",
        "HSM->cc",
        "HSM->gamgam",
        "HSM->gluglu",
        "HSM->mumu",
        "HSM->tautau",
        "HSM->tt",
    ]
    brs_extract = {}
    for tanb in tanbs:
        if str(tanb) not in brs_extract:
            brs_extract[str(tanb)] = {}
        for br in brs:
            higgs = br.split("-")[0]
            dm = br.split(">")[-1]
            if higgs not in brs_extract[str(tanb)]:
                brs_extract[str(tanb)][higgs] = {}
            brs_extract[str(tanb)][higgs][dm] = mssm_inputs.br(br, mA, tanb)

    yaml.dump({str(mA): brs_extract}, open("data/higgs_branching_ratios_mh125.yaml", "w"))


if __name__ == "__main__":
    main()
