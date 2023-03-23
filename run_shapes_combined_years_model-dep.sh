#!/bin/bash

TAG=$1
MODE=$2
b_only=$3
[[ -z ${b_only} ]] && b_only="1"

defaultdir=analysis_2022_02_28/$TAG
[[ ! -d ${defaultdir} ]] && mkdir -p ${defaultdir}
[[ ! -d ${defaultdir}/logs ]] && mkdir -p ${defaultdir}/logs
defaultdir=$(readlink -f analysis_2022_02_28/$TAG)
analysis="bsm-model-dep-full"
datacarddir=${defaultdir}/datacards_${analysis}

mass="130"
# mass="1200"

### Datacard creation ###
case "$MODE" in
    "datacards")
        morph_parallel.py --output ${defaultdir}/datacards \
                          --analysis ${analysis} \
                          --sub-analysis="sm-like-light" \
                          --hSM-treatment="hSM-in-bg" \
                          --categorization="with-sm-ml" \
                          --sm-like-hists="sm125" \
                          --sm-gg-fractions data/higgs_pt_reweighting_fullRun2.root \
                          --additional-arguments "--auto_rebin=1 --real_data=1 --manual_rebin=1 --split_sm_signal_cat=1 --enable_bsm_lowmass=1 --cbyear_plot=true" \
                          --eras "2016,2017,2018" \
                          --category-list input/mssm_new_categories.txt \
                          --variable "mt_tot_puppi" \
                          --parallel 8 \
                          |& tee ${defaultdir}/logs/morph_mssm_log.txt
        # Append autoMCStats command to each category by hand
        for dir in $(find analysis_2022_02_28/model-dep_full_with-sm-ml_hSM-in-bg_2022_04_29_mh125_cmbShapes/datacards_bsm-model-dep-full/ -maxdepth 1 -mindepth 1 -type d -name "htt_*"); do
            for file in ${dir}/htt_*.txt; do
                base=$(basename $file)
                cat=$(echo $base | cut -d"." -f1)
                echo "$cat autoMCStats 0 0 1" >> $file
            done
        done
        ;;

    "shapes")
        # for chan in lt; do
        for chan in "em" "lt" "tt"; do
          bins=(32 35)
          [[ ${chan} == "lt" ]] && bins+=(33 36)
          [[ ${chan} == "em" ]] && bins+=(33 34 36 37)
          for bin in ${bins[@]}; do
              fit_directory="analysis_2022_02_28/model-dep_full_with-sm-ml_hSM-in-bg_2022_04_29_mh125/datacards_bsm-model-dep-full/combined/cmb/"
              outfile="shapes_cbyears_${chan}_${bin}_mt_tot.root"
              fitfile="fitDiagnostics.combined-cmb.bestFit.mA1200,tanb17.root"
              echo "Doing (mt_tot) bin: htt_${chan}_${bin}"
              # combineTool.py -M T2W -o ws_mh125_cmb.root \
              # -P CombineHarvester.MSSMvsSMRun2Legacy.MSSMvsSM:MSSMvsSM \
              # --PO filePrefix=${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/data/ \
              # --PO replace-with-SM125=1 \
              # --PO hSM-treatment="hSM-in-bg" \
              # --PO modelFile="13,Run2017,mh125_13.root" \
              # --PO minTemplateMass=60 \
              # --PO maxTemplateMass=3500 \
              # --PO MSSM-NLO-Workspace=${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/data/higgs_pt_reweighting_fullRun2.root \
              # --PO sm-predictions=${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/sm_predictions_13TeV.json \
              # --PO qqh-pred-from-scaling=0 \
              # -i ${datacarddir}/htt_${chan}_${bin} \
              # --parallel 8 \
              # |& tee ${defaultdir}/logs/workspace_combined-shapes_${MODEL}.txt

              fit="fit_s"
              freeze=""
              if [[ "${b_only}" == "1" ]]; then
                  fit="fit_b"
                  outfile="shapes_cbyears_bOnly_${chan}_${bin}_mt_tot.root"
                  freeze="--freeze r=1,x=1,mA=1200,tanb=17"
              fi
              chan_repl=${chan}
              [[ ${chan} == "lt" ]] && chan_repl="mt"
              PostFitShapesFromWorkspace -w ${datacarddir}/htt_${chan}_${bin}/ws_mh125_cmb.root \
                                         -d ${datacarddir}/htt_${chan}_${bin}/combined.txt.cmb \
                                         --fitresult ${fit_directory}/${fitfile}:${fit} \
                                         -o ${datacarddir}/${outfile} \
                                         --skip-prefit=true  \
                                         --mass ${mass} \
                                         --total-shapes=true \
                                         --postfit ${freeze} &
                                         # -d ${datacarddir}/htt_${chan}_${bin}/combined.txt.cmb \
            done
        done
        wait
        ;;

    *)
        echo "[ERROR] Given mode $MODE not known. Aborting..."
        exit 1
        ;;
esac
