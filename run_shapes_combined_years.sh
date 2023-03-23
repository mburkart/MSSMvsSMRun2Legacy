#!/bin/bash

TAG=$1
MODE=$2
b_only=$3
[[ -z ${b_only} ]] && b_only="1"

defaultdir=analysis_2022_02_28/$TAG
[[ ! -d ${defaultdir} ]] && mkdir -p ${defaultdir}
[[ ! -d ${defaultdir}/logs ]] && mkdir -p ${defaultdir}/logs
defaultdir=$(readlink -f analysis_2022_02_28/$TAG)
analysis="bsm-model-indep"
datacarddir=${defaultdir}/datacards_${analysis}

# mass="3200"
mass="1200"

### Datacard creation ###
case "$MODE" in
    "datacards")
        morph_parallel.py --output ${defaultdir}/datacards \
                          --analysis ${analysis} \
                          --eras "2016,2017,2018" \
                          --category-list input/mssm_classic_categories_nobtag.txt \
                          --variable "mt_tot_puppi" \
                          --sm-gg-fractions data/higgs_pt_reweighting_fullRun2_v2.root \
                          --parallel 8 \
                          --additional-arguments="--auto_rebin=1 --manual_rebin=1 --real_data=1 --cbyear_plot=true --cbyear_plot_mass=${mass}" \
                          --sub-analysis="none" \
                          --hSM-treatment="hSM-in-bg" \
                          --categorization="classic" \
                          --sm-like-hists="bsm" |& tee ${defaultdir}/logs/morph_mssm_log.txt
        morph_parallel.py --output ${defaultdir}/datacards \
                          --analysis ${analysis} \
                          --eras "2016,2017,2018" \
                          --category-list input/mssm_classic_categories_btag.txt \
                          --variable "mt_tot_puppi" \
                          --sm-gg-fractions data/higgs_pt_reweighting_fullRun2_v2.root \
                          --parallel 8 \
                          --additional-arguments="--auto_rebin=1 --manual_rebin=1 --real_data=1 --cbyear_plot=true --cbyear_plot_mass=${mass}" \
                          --sub-analysis="none" \
                          --hSM-treatment="hSM-in-bg" \
                          --categorization="classic" \
                          --sm-like-hists="bsm" |& tee -a ${defaultdir}/logs/morph_mssm_log.txt
        morph_parallel.py --output ${defaultdir}/datacards \
                          --analysis ${analysis} \
                          --eras "2016,2017,2018" \
                          --category-list input/mssm_classic_categories_cr.txt \
                          --variable "mt_tot_puppi" \
                          --sm-gg-fractions data/higgs_pt_reweighting_fullRun2_v2.root \
                          --parallel 1 \
                          --additional-arguments="--auto_rebin=1 --manual_rebin=1 --real_data=1 --cbyear_plot=true --cbyear_plot_mass=${mass}" \
                          --sub-analysis="none" \
                          --hSM-treatment="hSM-in-bg" \
                          --categorization="classic" \
                          --sm-like-hists="bsm" |& tee -a ${defaultdir}/logs/morph_mssm_log.txt
        ;;

    "shapes")
        # for chan in "lt"; do
        for chan in "em" "lt" "tt"; do
          bins=(32 35)
          [[ ${chan} == "lt" ]] && bins+=(33 36)
          [[ ${chan} == "em" ]] && bins+=(33 34 36 37)
          for bin in ${bins[@]}; do
              # fit_directory="analysis_2022_02_28/model-indep_classic_2022-08-08_hSM-in-bg/datacards_bsm-model-indep/combined/cmb/"
              fit_directory="analysis_2022_02_28/model-indep_classic_2022-08-08_hSM-in-bg_cmbShapes/datacards_bsm-model-indep/htt_mt_tot/"
              outfile="shapes_cbyears_${chan}_${bin}_mt_tot.root"
              # fitfile="fitDiagnostics.combined-cmb.bestFit.mH${mass}.root"
              fitfile="fitDiagnostics.combined-cmb.bestFit.mH${mass}.combined_r.root"
              echo "Doing (mt_tot) bin: htt_${chan}_${bin}"
              # combineTool.py -M T2W \
              #                -o "ws.root" \
              #                -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel \
              #                --PO '"map=^.*/ggh_(i|t|b).?$:r_ggH[0,0,200]"' \
              #                --PO '"map=^.*/bbh$:r_bbH[0,0,200]"' \
              #                --PO '"map=^.*/qqX$:r_qqX[0]"' \
              #                --PO '"map=^.*/ggX_(i|t|b).?$:r_ggX[0,0,200]"'  \
              #                -i ${datacarddir}/htt_${chan}_${bin}_mt_tot \
              #                -m ${mass} \
              #                --parallel 8

              fit="fit_s"
              freeze=""
              if [[ "${b_only}" == "1" ]]; then
                  fit="fit_b"
                  outfile="shapes_cbyears_bOnly_${chan}_${bin}_mt_tot-combinedFit.root"
                  if [[ "$mass" == "1200" ]]; then
                      freeze="--freeze r_bbH=0.001,r_ggH=0.0032"
                  elif [[ "$mass" == "350" ]]; then
                      freeze="--freeze r_bbH=0.1,r_ggH=0.1"
                  elif [[ "$mass" == "3200" ]]; then
                      freeze="--freeze r_bbH=0.0005,r_ggH=0.0005"
                  else
                      freeze="--freeze r_bbH=3.0,r_ggH=5.4"
                  fi
              fi
              PostFitShapesFromWorkspace -w ${datacarddir}/htt_${chan}_${bin}_mt_tot/ws.root \
                                         -d ${datacarddir}/htt_${chan}_${bin}_mt_tot/combined.txt.cmb \
                                         --fitresult ${fit_directory}/${fitfile}:${fit} \
                                         -o ${datacarddir}/${outfile} \
                                         --skip-prefit=true  \
                                         --mass ${mass} \
                                         --total-shapes=true \
                                         --postfit ${freeze} &
            done
        done
        wait
        ;;

    *)
        echo "[ERROR] Given mode $MODE not known. Aborting..."
        exit 1
        ;;
esac
