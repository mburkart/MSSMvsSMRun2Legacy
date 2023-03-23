#!/bin/bash

# tag_high="2022-04-12"
tag_high="2022-06-07"
tag_low="-lowmass_2022_06_07"
defaultdir="analysis_2022_02_28/model-indep_classic_${tag_high}_hSM-in-bg/"

xrange () {
    [ "$#" != 1 ] && exit
    case $1 in
        "60")
            echo 8.
            ;;
        "80")
            echo 4.
            ;;
        "95")
            echo 25.
            ;;
        "100")
            echo 15.
            ;;
        "120")
            echo 3.
            ;;
        "125")
            echo 2.
            ;;
        "130")
            echo 1.2
            ;;
        "140")
            echo 0.8
            ;;
        "160")
            echo 0.5
            ;;
        "180")
            echo 0.4
            ;;
        "200")
            echo 0.3
            ;;
        "250")
            echo 0.12
            ;;
        "300")
            echo 0.08
            ;;
        "350")
            echo 0.05
            ;;
        "400")
            echo 0.05
            ;;
        "450")
            echo 0.05
            ;;
        "500")
            echo 0.03
            ;;
        "600")
            echo 0.014
            ;;
        "700")
            echo 0.01
            ;;
        "800")
            echo 0.008
            ;;
        "900")
            echo 0.01
            ;;
        "1000")
            echo 0.01
            ;;
        "1200")
            echo 0.007
            ;;
        "1400")
            echo 0.005
            ;;
        "1600")
            echo 0.003
            ;;
        "1800")
            echo 0.0018
            ;;
        "2000")
            echo 0.0014
            ;;
        "2300")
            echo 0.001
            ;;
        "2600")
            echo 0.0008
            ;;
        "2900")
            echo 0.0006
            ;;
        "3200")
            echo 0.0005
            ;;
        "3500")
            echo 0.0005
            ;;
        *)
            exit 1
            ;;
    esac
}

yrange () {
    [ "$#" != 1 ] && exit
    case $1 in
        "60")
            echo 50.
            ;;
        "80")
            echo 20.
            ;;
        "95")
            echo 6.
            ;;
        "100")
            echo 4.
            ;;
        "120")
            echo 1.
            ;;
        "125")
            echo 0.8
            ;;
        "130")
            echo 0.6
            ;;
        "140")
            echo 0.5
            ;;
        "160")
            echo 0.4
            ;;
        "180")
            echo 0.3
            ;;
        "200")
            echo 0.35
            ;;
        "250")
            echo 0.12
            ;;
        "300")
            echo 0.08
            ;;
        "350")
            echo 0.06
            ;;
        "400")
            echo 0.05
            ;;
        "450")
            echo 0.06
            ;;
        "500")
            echo 0.045
            ;;
        "600")
            echo 0.022
            ;;
        "700")
            echo 0.012
            ;;
        "800")
            echo 0.008
            ;;
        "900")
            echo 0.006
            ;;
        "1000")
            echo 0.005
            ;;
        "1200")
            echo 0.003
            ;;
        "1400")
            echo 0.002
            ;;
        "1600")
            echo 0.0016
            ;;
        "1800")
            echo 0.0014
            ;;
        "2000")
            echo 0.0012
            ;;
        "2300")
            echo 0.001
            ;;
        "2600")
            echo 0.0008
            ;;
        "2900")
            echo 0.0006
            ;;
        "3200")
            echo 0.0006
            ;;
        "3500")
            echo 0.0006
            ;;
        *)
            exit 1
            ;;
    esac
}
pushd ${defaultdir}/ggH_bbH_scan_ind/
pushd
# Create database entries for high-mass analysis
for mass in 250 300 350 400 450 500 600 700 800 900 1000 1200 1400 1600 1800 2000 2300 2600 2900 3200 3500; do
    python scripts/create_likelihood_database.py ${defaultdir}/ggH_bbH_scan_ind/condor/higgsCombine.ggH-bbH.POINTS.*.mH${mass}.root --output ${defaultdir}/ggH_bbH_scan_ind/scan_values_mH${mass}.txt

    # Make plots of the created trees to be able to compare them to the original plots
    pushd
    python ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/plotting/plotMultiDimFit.py \
        --title-right="138 fb^{-1} (13 TeV)" \
        --cms-sub Testing \
        --mass ${mass} \
        -o test_2D_limit_mH${mass}_Testing \
        --x-title "#sigma#font[42]{(gg#phi)}#font[52]{B}#font[42]{(#phi#rightarrow#tau#tau)} (pb)" \
        --y-title "#sigma#font[42]{(bb#phi)}#font[52]{B}#font[42]{(#phi#rightarrow#tau#tau)} (pb)" \
        --x-axis-max $(xrange ${mass}) \
        --y-axis-max $(yrange ${mass}) \
        scan_values_mH${mass}.root
    pushd
done

# Remove results directory for high-mass analysis from stack
pushd; popd

# Create database entries for the low-mass analysis
defaultdir="analysis_2022_02_28/model-indep_classic${tag_low}_hSM-in-bg/"

pushd ${defaultdir}/ggH_bbH_scan_ind/ && pushd
for mass in 60 80 95 100 120 125 130 140 160 180 200; do
    python scripts/create_likelihood_database.py ${defaultdir}/ggH_bbH_scan_ind/condor/higgsCombine.ggH-bbH.POINTS.*.mH${mass}.root --output ${defaultdir}/ggH_bbH_scan_ind/scan_values_mH${mass}.txt

    # Make plots of the created trees to be able to compare them to the original plots
    pushd
    python ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/plotting/plotMultiDimFit.py \
        --title-right="138 fb^{-1} (13 TeV)" \
        --cms-sub Testing \
        --mass ${mass} \
        -o test_2D_limit_mH${mass}_Testing \
        --x-title "#sigma#font[42]{(gg#phi)}#font[52]{B}#font[42]{(#phi#rightarrow#tau#tau)} (pb)" \
        --y-title "#sigma#font[42]{(bb#phi)}#font[52]{B}#font[42]{(#phi#rightarrow#tau#tau)} (pb)" \
        --x-axis-max $(xrange ${mass}) \
        --y-axis-max $(yrange ${mass}) \
        --debug test_scan_values_mH${mass}_Testing.root \
        scan_values_mH${mass}.root
    pushd
done

pushd && popd
