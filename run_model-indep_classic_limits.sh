#!/bin/bash
# based on https://github.com/KIT-CMS/MSSMvsSMRun2Legacy/tree/ntuple_processor
ulimit -s unlimited

TAG=$1
MODE=$2
if [[ $TAG == "auto" ]]; then
    TAG="cmb_ind"
fi

defaultdir=analysis_2022_02_28/$TAG
analysis="bsm-model-indep"
hSM_treatment="hSM-in-bg"
# hSM_treatment="no-hSM-in-bg"
categorization="classic"
sm_like_hists="bsm"
[[ ! -d ${defaultdir} ]] && mkdir -p ${defaultdir}
[[ ! -d ${defaultdir}/logs ]] && mkdir -p ${defaultdir}/logs
[[ ! -d ${defaultdir}/limits/condor ]] && mkdir -p ${defaultdir}/limits/condor
[[ ! -d ${defaultdir}/limits_ind/condor ]] && mkdir -p ${defaultdir}/limits_ind/condor
defaultdir=$(readlink -f analysis_2022_02_28/$TAG)
datacarddir=${defaultdir}/datacards_${analysis}
freeze="MH=1200,r_ggH=0.005,r_bbH=0.0015"
identifier_toy_submit=$(date +%Y_%m_%d)
[[ -z $3 ]] || identifier_toy_submit=$3

xrange () {
    [ "$#" != 1 ] && exit
    case $1 in
        "60")
            echo 18
            ;;
        "80")
            echo 24
            ;;
        "100")
            echo 30
            ;;
        "120")
            echo 14
            ;;
        "125")
            echo 10
            ;;
        "130")
            echo 10
            ;;
        "140")
            echo 5
            ;;
        "160")
            echo 2.5
            ;;
        "180")
            echo 1
            ;;
        "200")
            echo 0.45
            ;;
        "250")
            echo 0.12
            ;;
        "300")
            echo 0.075
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
            echo 40
            ;;
        "80")
            echo 14
            ;;
        "100")
            echo 4
            ;;
        "120")
            echo 2.5
            ;;
        "125")
            echo 2
            ;;
        "130")
            echo 1.4
            ;;
        "140")
            echo 1.3
            ;;
        "160")
            echo 1
            ;;
        "180")
            echo 0.6
            ;;
        "200")
            echo 0.3
            ;;
        "250")
            echo 0.12
            ;;
        "300")
            echo 0.07
            ;;
        "350")
            echo 0.06
            ;;
        "400")
            echo 0.055
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
            echo 0.0018
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
            echo 0.0007
            ;;
        "3200")
            echo 0.00065
            ;;
        "3500")
            echo 0.0006
            ;;
        *)
            exit 1
            ;;
    esac
}

if [[ $MODE == "initial" ]]; then
    ############
    # morphing
    ############
    morph_parallel.py --output ${defaultdir}/datacards \
        --analysis ${analysis} \
        --sub-analysis "none" \
        --hSM-treatment ${hSM_treatment} \
        --categorization ${categorization} \
        --sm-like-hists ${sm_like_hists} \
        --eras 2016,2017,2018 \
        --category-list ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_classic_categories.txt \
        --additional-arguments "--auto_rebin=1 --real_data=1 --manual_rebin=1" \
        --variable mt_tot_puppi \
        --sm-gg-fractions ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/data/higgs_pt_reweighting_fullRun2.root \
        --parallel 10 2>&1 | tee -a ${defaultdir}/logs/morph_mssm_log.txt

    ############
    # combining outputs
    ############
    mkdir -p ${datacarddir}/combined/cmb/
    rsync -av --progress ${datacarddir}/201?/htt_*/* ${datacarddir}/combined/cmb/ 2>&1 | tee -a ${defaultdir}/logs/copy_datacards.txt
    for ERA in 2016 2017 2018; do
        for CH in et mt tt em; do
            mkdir -p ${datacarddir}/${ERA}/${CH}/
            rsync -av --progress ${datacarddir}/${ERA}/htt_${CH}*/* ${datacarddir}/${ERA}/${CH}/ 2>&1 | tee -a ${defaultdir}/logs/copy_datacards.txt
        done
        mkdir -p ${datacarddir}/${ERA}/cmb/
        rsync -av --progress ${datacarddir}/${ERA}/htt_*/* ${datacarddir}/${ERA}/cmb/ 2>&1 | tee -a ${defaultdir}/logs/copy_datacards.txt
    done

    # Perform checks on the produced datacards

    # Run datacard check from Higgs PAG
    combineTool.py -M T2W \
        -o ws.root \
        -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel \
        --PO '"map=^.*/ggh_(i|t|b).?$:r_ggH[0,0,200]"' \
        --PO '"map=^.*/bbh$:r_bbH[0,0,200]"' \
        -i ${datacarddir}/restore_binning/ \
        -m 110 \
        --X-allow-no-signal --just-check-physics-model

    ValidateDatacards.py ${datacarddir}/restore_binning/combined.txt.cmb \
        --jsonFile ${datacarddir}/restore_binning/validation_restore_binning.json \
        --mass 110 --printLevel 1

    # Check number of produced datacards
    EXPECTED=$(((4+4+2+7)*3))
    if [[ $(ls ${datacarddir}/combined/cmb/*.txt | wc -l) != $EXPECTED ]]; then
        echo -e "\033[0;31m[ERROR]\033[0m Not all datacards have been created or written. Please check the logs..."
        echo "Expected ${EXPECTED} datacards written but found only $(ls ${datacarddir}/combined/cmb/ | wc -l) in the combined directory."
    fi

elif [[ $MODE == "ws" ]]; then
    ############
    # workspace creation
    ############

    combineTool.py -M T2W -o "ws.root" \
    -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel \
    --PO '"map=^.*/ggh_(i|t|b).?$:r_ggH[0,0,200]"' \
    --PO '"map=^.*/bbh$:r_bbH[0,0,200]"' \
    -i ${datacarddir}/combined/cmb/ \
    -m 125.0 --parallel 4 | tee -a ${defaultdir}/logs/workspace_independent.txt

elif [[ $MODE == "setup" ]]; then

    ############
    # job setup creation
    ############
    cd ${defaultdir}/limits_ind/condor
    combineTool.py -m "60,80,100,120,125,130,140,160,180,200,250,300,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500" \
    -M AsymptoticLimits \
    --rAbsAcc 0 \
    --rRelAcc 0.0005 \
    --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_boundaries.json \
    --setParameters r_ggH=0,r_bbH=0 \
    --redefineSignalPOIs r_bbH \
    -d ${datacarddir}/combined/cmb/ws.root \
    --there -n ".bbH" \
    --job-mode condor \
    --dry-run \
    --task-name bbH_full_cmb \
    --X-rtd MINIMIZER_analytic \
    --cminDefaultMinimizerStrategy 0 \
    --cminDefaultMinimizerTolerance 0.01 \
    -v 1 | tee -a ${defaultdir}/logs/job_setup_modelind_bbh.txt

    combineTool.py -m "60,80,100,120,125,130,140,160,180,200,250,300,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500" \
    -M AsymptoticLimits \
    --rAbsAcc 0 \
    --rRelAcc 0.0005 \
    --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_boundaries.json \
    --setParameters r_ggH=0,r_bbH=0 \
    --redefineSignalPOIs r_ggH \
    -d ${datacarddir}/combined/cmb/ws.root \
    --there -n ".ggH" \
    --job-mode condor \
    --dry-run \
    --task-name ggH_full_cmb \
    --X-rtd MINIMIZER_analytic \
    --cminDefaultMinimizerStrategy 0 \
    --cminDefaultMinimizerTolerance 0.01 \
    -v 1 | tee -a ${defaultdir}/logs/job_setup_modelind_ggh.txt

elif [[ $MODE == "ws-gof" ]]; then
    for CH in et mt tt em; do
        rsync -av --progress ${datacarddir}/201?/htt_${CH}_*/* ${datacarddir}/combined/${CH}/ 2>&1 | tee -a ${defaultdir}/logs/copy_datacards.txt
    done
    # Copy ttbar control region to every channel to include it in the workspaces
    for ERA in 2016 2017 2018; do
        for CH in et mt tt; do
            rsync -av --progress ${datacarddir}/${ERA}/htt_em_2_${ERA}/* ${datacarddir}/${ERA}/${CH}/ 2>&1 | tee -a ${defaultdir}/logs/copy_datacards.txt
            rsync -av --progress ${datacarddir}/${ERA}/htt_em_2_${ERA}/* ${datacarddir}/combined/${CH}/ 2>&1 | tee -a ${defaultdir}/logs/copy_datacards.txt
        done
    done
    ############
    # workspace creation for GoF tests
    ############

    combineTool.py -M T2W -o "ws-gof.root" \
    -i ${datacarddir}/*/{et,mt,tt,em,cmb}/ \
    --channel-masks \
    -m 125.0 --parallel 8 | tee -a ${defaultdir}/logs/workspace_gof_independent.txt

elif [[ $MODE == "ws-plot" ]]; then
    ###############
    # workspace production for plots
    ###############
    combineTool.py -M T2W -o "ws.root" \
    -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel \
    --PO '"map=^.*/ggh_(i|t|b).?$:r_ggH[-50,200]"' \
    --PO '"map=^.*/bbh$:r_bbH[-50,0,200]"' \
    --X-allow-no-signal \
    -i ${datacarddir}/201?/htt_*/ \
    -m 125.0 \
    --parallel 8 | tee -a ${defaultdir}/logs/workspace_plots_independent.txt

elif [[ $MODE == "submit" ]]; then
    ############
    # job submission
    ############
    cd ${defaultdir}/limits_ind/condor
    condor_submit condor_bbH_full_cmb.sub
    condor_submit condor_ggH_full_cmb.sub

elif [[ $MODE == "submit-local" ]]; then
    ############
    # job submission
    ############
    cp scripts/run_limits_locally.py ${defaultdir}/limits_ind/condor
    cd ${defaultdir}/limits_ind/condor
    python run_limits_locally.py --cores 10 --njobs 31 --taskname condor_bbH_full_cmb.sh
    python run_limits_locally.py --cores 10 --njobs 31 --taskname condor_ggH_full_cmb.sh

elif [[ $MODE == "collect" ]]; then
    for p in gg bb
    do
        combineTool.py -M CollectLimits ${datacarddir}/combined/cmb/higgsCombine.${p}H*AsymptoticLimits*.root \
        --use-dirs \
        -o ${datacarddir}/combined/cmb/mssm_${p}H.json

        reldefaultdir=$(realpath --relative-to="$PWD" "${defaultdir}")
        ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/scripts/plotMSSMLimits_for_thesis.py \
            --title-right "138 fb^{-1} (13 TeV)" \
            --x-title "m_{#phi} (GeV)" \
            --process "${p}#phi" \
            --y-axis-min 0.0001 \
            --y-axis-max 100.0 \
            --show exp ${datacarddir}/combined/cmb/mssm_${p}H_cmb.json \
            --output ${reldefaultdir}/limits_ind/mssm_model-independent-expected_${p}H_cmb \
            --logx \
            --logy
    done

elif [[ "$MODE" == "prepare-hybrid" ]]; then
    [[ ! -d ${defaultdir}/limits_ind_toys_v2/condor ]] && mkdir -p ${defaultdir}/limits_ind_toys_v2/condor
    pushd ${defaultdir}/limits_ind_toys_v2/condor
    # Trim down the results file to the mass range we are interested in.
    # for p in gg bb; do
    for p in gg; do
        # python ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/scripts/trim_results_json.py -i ${datacarddir}/combined/cmb/mssm_${p}H_cmb.json \
        #     --min-mass 2300

        # Run the combineTool commands to create the jobs
        combineTool.py -M HybridNewGridComp \
            ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_hybrid_grid_model-indep_from-asymptotic_${p}H.json \
            --cycles 250 \
            --datacard ${datacarddir}/combined/cmb/ws.root \
            --job-mode 'condor' --task-name ${p}H_full_cmb_hybrid_from_asymptotic --dry-run \
            --from-asymptotic ${datacarddir}/combined/cmb/mssm_${p}H_cmb_trimmed.json
    done

elif [[ "$MODE" == "check-hybrid" ]]; then
    [[ ! -d ${defaultdir}/limits_ind_toys_v2/condor ]] && echo "Please run preparation step beforehand." && exit 1
    pushd ${defaultdir}/limits_ind_toys_v2/condor
    # for p in gg bb; do
    for p in gg; do
        # Run the combineTool commands to create the jobs
        combineTool.py -M HybridNewGridComp \
            ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_hybrid_grid_model-indep_from-asymptotic_${p}H.json \
            --cycles 100 \
            --datacard ${datacarddir}/combined/cmb/ws.root \
            --job-mode 'condor' --task-name ${p}H_full_cmb_hybrid_from_asymptotic --dry-run \
            --from-asymptotic ${datacarddir}/combined/cmb/mssm_${p}H_cmb_trimmed.json
    done

elif [[ "$MODE" == "submit-hybrid-gc" ]]; then
    for p in gg bb; do
        gcworkdir=${defaultdir}/limits_ind_toys_v2/r_${p}H/gc_condor_${identifier_toy_submit}
        mkdir -p ${gcworkdir}
        python scripts/build_gc_job.py \
            --combine-script ${defaultdir}/limits_ind_toys_v2/condor/condor_${p}H_full_cmb_hybrid_from_asymptotic.sh \
            --workspace ${datacarddir}/combined/cmb/ws.root \
            --workdir ${gcworkdir} \
            --tag ${p}H_full_cmb_hybrid_from_asymptotic \
            --se-path /storage/gridka-nrg/$(whoami)/gc_storage/combine/${p}H_full_cmb_hybrid_from_asymptotic_${identifier_toy_submit}

        echo "Submit with ${CMSSW_BASE}/src/grid-control/go.py ${gcworkdir}/${p}H_full_cmb_hybrid_from_asymptotic.conf -Gc -m 3"
        # ${CMSSW_BASE}/src/grid-control/go.py ${gcworkdir}/${p}H_full_cmb_hybrid_from_asymptotic_${identifier_toy_submit}.conf -G -m 3
    done


elif [[ "$MODE" == "copy-results-gc-hybrid" ]]; then
    ############
    # job submission
    ############
    for p in gg bb; do
        rsync -avhP /storage/gridka-nrg/$(whoami)/gc_storage/combine/${p}H_full_cmb_hybrid_from_asymptotic_${identifier_toy_submit}/output/ ${defaultdir}/limits_ind_toys_v2/condor
    done

elif [[ "$MODE" == "collect-hybrid" ]]; then
    pushd ${defaultdir}/limits_ind_toys_v2/condor
    # for p in gg bb; do
    for p in gg; do
        # Run the combineTool commands to create the jobs
        combineTool.py -M HybridNewGridComp \
            ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_hybrid_grid_model-indep_from-asymptotic_${p}H.json \
            --cycles 0 \
            --job-mode 'condor' --task-name "test_merge_command_from_asymptotic_${p}H" --dry-run \
            --datacard ${datacarddir}/combined/cmb/ws.root \
            --from-asymptotic ${datacarddir}/combined/cmb/mssm_${p}H_cmb_trimmed.json \
            --output
            # --job-mode 'interactive' \
    done

elif [[ $MODE == "prefit-plots" ]]; then
    #####################
    # Extract prefit shapes.
    #####################
    for era in 2016 2017 2018; do
        prefit_postfit_shapes_parallel.py --datacard_pattern "${datacarddir}/${era}/htt_em_2_*/combined.txt.cmb" \
                                          --workspace_name ws.root \
                                          --output_name prefit_shapes_${freeze}.root \
                                          --parallel 8 | tee -a ${defaultdir}/logs/extract_model_independent_shapes-combined-${freeze}.log
        prefit_postfit_shapes_parallel.py --datacard_pattern "${datacarddir}/${era}/htt_*_3*/combined.txt.cmb" \
                                          --workspace_name ws.root \
                                          --freeze_arguments "--freeze ${freeze}" \
                                          --output_name prefit_shapes_${freeze}.root \
                                          --parallel 8 | tee -a ${defaultdir}/logs/extract_model_independent_shapes-combined-${freeze}.log
    done
    hadd -f ${datacarddir}/combined/cmb/prefit_shapes_${freeze}.root ${datacarddir}/201?/htt_*/prefit_shapes_${freeze}.root | tee -a ${defaultdir}/logs/extract_model_independent_shapes-combined-${freeze}.log

    for era in 2016 2017 2018; do
        bash plotting/plot_shapes_mssm_model_independent.sh \
            ${era} \
            "${datacarddir}/combined/cmb/prefit_shapes_${freeze}.root" \
            "${datacarddir}/plots/prefit_shapes_$(echo ${freeze} | sed 's/=//g; s/\./p/g')/" \
            et,mt,tt,em \
            $(echo $freeze | cut -d, -f1 | cut -d= -f2) \
            $(echo $freeze | cut -d, -f2 | cut -d= -f2)
    done

elif [[ $MODE == "fit-for-plots" ]]; then
    mass="1200"
    combineTool.py -M FitDiagnostics \
        -d ${datacarddir}/combined/cmb/ws.root \
        -m ${mass} \
        --setParameters r_ggH=0,r_bbH=0 --setParameterRange r_ggH=-0.03,0.03:r_bbH=-0.03,0.03 \
        --redefineSignalPOIs r_ggH,r_bbH \
        --X-rtd MINIMIZER_analytic \
        --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 \
        --robustHesse 1 \
        -n .combined-cmb.bestFit.secondRun.r_ggH.r_bbH.mH${mass} \
        --there \
        -v 1 \
        |& tee ${defaultdir}/logs/fitDiagnostics_mH${mass}.log
        # --redefineSignalPOIs r_ggH --freezeParameters r_bbH,r_ggH \

elif [[ $MODE == "postfit-plots" ]]; then
    ######################
    # Extract postfit shapes.
    #####################
    # fitfile=${datacarddir}/combined/cmb/fitDiagnostics.combined-cmb.for_shape_unblinding.root
    fitfile=${datacarddir}/combined/cmb/fitDiagnostics.combined-cmb.bestFit.root
    for era in 2016 2017 2018; do
        prefit_postfit_shapes_parallel.py --datacard_pattern "${datacarddir}/${era}/htt_em_2_*/combined.txt.cmb" \
                                          --workspace_name ws.root \
                                          --fit_arguments "-f ${fitfile}:fit_b --postfit --sampling --skip-prefit" \
                                          --output_name postfit_shapes_${freeze}.root \
                                          --parallel 8 | tee -a ${defaultdir}/logs/extract_model_independent_shapes-postfit-combined-${freeze}.log
        prefit_postfit_shapes_parallel.py --datacard_pattern "${datacarddir}/${era}/htt_*_3*_*/combined.txt.cmb" \
                                          --workspace_name ws.root \
                                          --freeze_arguments "--freeze ${freeze}" \
                                          --fit_arguments "-f ${fitfile}:fit_b --postfit --sampling --skip-prefit" \
                                          --output_name postfit_shapes_${freeze}.root \
                                          --parallel 8 | tee -a ${defaultdir}/logs/extract_model_independent_shapes-postfit-combined-${freeze}.log
    done

    hadd -f ${datacarddir}/combined/cmb/postfit_shapes_${freeze}.root ${datacarddir}/201?/htt_*/postfit_shapes_${freeze}.root | tee -a ${defaultdir}/logs/extract_model_independent_shapes-postfit-combined-${freeze}.log

    for era in 2016 2017 2018; do
        bash plotting/plot_shapes_mssm_model_independent.sh \
            ${era} \
            "${datacarddir}/combined/cmb/postfit_shapes_${freeze}.root" \
            "${datacarddir}/plots/postfit_shapes_$(echo ${freeze} | sed 's/=//g; s/\./p/g')/" \
            et,mt,tt,em \
            $(echo $freeze | cut -d, -f1 | cut -d= -f2) \
            $(echo $freeze | cut -d, -f2 | cut -d= -f2)
    done

elif [[ $MODE == "prepare-ggH-bbH-scan" ]]; then
    [[ ! -d ${defaultdir}/ggH_bbH_scan_ind/condor ]] && mkdir -p ${defaultdir}/ggH_bbH_scan_ind/condor
    cd ${defaultdir}/ggH_bbH_scan_ind/condor
    # Run 2D likelihood scans for r_ggH and r_bbH
    combineTool.py -M MultiDimFit \
        --algo grid --points 4000 --alignEdges 1 --split-points 50 \
        -m "60,80,100,120,125,130,140,160,180,200" \
        --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_ggH_bbH_2D_boundaries_lowmass_mttot.json \
        --setParameters r_ggH=0,r_bbH=0 --redefineSignalPOIs r_ggH,r_bbH \
        -d ${datacarddir}/combined/cmb/ws.root \
        --job-mode condor --dry-run --task-name ggH_bbH_likelihood_scan \
        --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 \
        --cminFallbackAlgo Minuit2,Migrad,0:0.1 \
        -n ".ggH-bbH" \
        -v 1
        # -m "250,500,1000,1200,3500" \
        # -m "250,300,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500" \


elif [[ $MODE == "submit-ggH-bbH-scan" ]]; then
    cd ${defaultdir}/ggH_bbH_scan_ind/condor
    condor_submit condor_ggH_bbH_likelihood_scan.sub


elif [[ "$MODE" == "submit-ggH-bbH-scan-gc" ]]; then
    gcworkdir=${defaultdir}/ggH_bbH_scan_ind/gc_condor_${identifier_toy_submit}
    mkdir -p ${gcworkdir}
    python scripts/build_gc_job.py \
        --combine-script ${defaultdir}/ggH_bbH_scan_ind/condor/condor_ggH_bbH_likelihood_scan.sh \
        --workspace ${datacarddir}/combined/cmb/ws.root \
        --workdir ${gcworkdir} \
        --tag ggH_bbH_likelihood_scan \
        --se-path /storage/gridka-nrg/$(whoami)/gc_storage/combine/ggH_bbH_likelihood_scan_${identifier_toy_submit}

    echo "Submit with ${CMSSW_BASE}/src/grid-control/go.py ${gcworkdir}/ggH_bbH_likelihood_scan.conf -Gc -m 3"
    # ${CMSSW_BASE}/src/grid-control/go.py ${gcworkdir}/ggH_bbH_likelihood_scan_${identifier_toy_submit}.conf -G -m 3


elif [[ "$MODE" == "copy-results-ggH-bbH-scan" ]]; then
    rsync -avhP /storage/gridka-nrg/$(whoami)/gc_storage/combine/ggH_bbH_likelihood_scan_${identifier_toy_submit}/output/ ${defaultdir}/ggH_bbH_scan_ind/condor


elif [[ $MODE == "collect-ggH-bbH-scan" ]]; then
    cd ${defaultdir}/ggH_bbH_scan_ind/
    smexp=""
    # for mass in 250 300 350 400 450 500 600 700 800 900 1000 1200 1400 1600 1800 2000 2300 2600 2900 3200 3500; do
    for mass in 60 80 100 120 125 130 140 160 180 200; do
        [[ "$TAG" =~ NohSMinBackground$ ]] && smexp="--sm-exp ${datacarddir}/combined/cmb/higgsCombine.2D.SM1.bestfit.MultiDimFit.mH${mass}.root"
        for cmssub in "" "Supplementary"; do
            cmssubadd="_CMS"
            [[ "$cmssub" == "Preliminary" ]] && cmssubadd=""
            [[ "$cmssub" == "Supplementary" ]] && cmssubadd="_Supplementary"
            isBkg=1
            [[ "$TAG" =~ NohSMinBackground ]] && isBkg=0
            for int in 0 1; do
                if [[ $int -eq 1 ]]; then
                    int_arg="--interpolate-missing"
                    int_sub="_interpolated"
                else
                    int_arg=""
                    int_sub=""
                fi
                python ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/plotting/plotMultiDimFit_for_thesis.py \
                    --title-right="#font[62]{CMS} data 138 fb^{-1} (13 TeV)" \
                    --mass $mass \
                    -o 2D_limit_mH${mass}${cmssubadd}${int_sub} \
                    ${smexp} \
                    --debug-output test_mH${mass}${int_sub}.root \
                    --x-axis-max $(xrange $mass) --y-axis-max $(yrange $mass) \
                    ${int_arg} \
                    --x-title "#sigma#font[42]{(gg#phi)}#font[52]{B}#font[42]{(#phi#rightarrow#tau#tau)} (pb)" \
                    --y-title "#sigma#font[42]{(bb#phi)}#font[52]{B}#font[42]{(#phi#rightarrow#tau#tau)} (pb)" \
                    condor/higgsCombine.ggH-bbH.POINTS.*.mH${mass}.root
                    # --cms-sub=${cmssub} \
                    # --likelihood-database \
                    # --add-3sigma-contour \
            done
        done
    done

elif [[ $MODE == "ggH-bbH-scan-SM-expectation" ]]; then
    # TODO: This option only makes sense for the with hSM not in the background
    # Create asimov dataset for SM-expectation.
    combineTool.py -M MultiDimFit \
        --algo none \
        -m "125" \
        --setParameters r_ggH=0,r_bbH=0 --redefineSignalPOIs r_ggH,r_bbH \
        --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_ggH_bbH_2D_boundaries.json \
        -d $(dirname $defaultdir)/cmb_ind_hSMinBackground/datacards_bsm-model-indep/combined/cmb/ws.root \
        --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 \
        -t -1 --saveToys \
        --there -n ".2D.ToyDataset.SM1" \
        -v 1

    # Copy it to correct location
    rsync -av --progress $(dirname $defaultdir)/cmb_ind_hSMinBackground/datacards_bsm-model-indep/combined/cmb/higgsCombine.2D.ToyDataset.SM1.MultiDimFit.mH125.123456.root ${datacarddir}/combined/cmb/higgsCombine.2D.ToyDataset.SM1.MultiDimFit.mH125.123456.root

    pushd ${defaultdir}/ggH_bbH_scan_ind/
    # Run fits on this asimov dataset
    combineTool.py -M MultiDimFit \
        --algo none \
        -m "250,300,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500" \
        --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_ggH_bbH_2D_boundaries.json \
        --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 \
        --setParameters r_ggH=0,r_bbH=0 --redefineSignalPOIs r_ggH,r_bbH \
        -d ${datacarddir}/combined/cmb/ws.root \
        -t -1 --toysFile higgsCombine.2D.ToyDataset.SM1.MultiDimFit.mH125.123456.root \
        --job-mode condor --dry-run --task-name ggH_bbH_likelihood_SM1 --merge 3 \
        --there -n ".2D.SM1.bestfit"
    popd

elif [[ $MODE == "setup-sig" ]]; then
    [[ ! -d ${defaultdir}/significance_ind/condor ]] && mkdir -p ${defaultdir}/significance_ind/condor
    cd ${defaultdir}/significance_ind/condor
    combineTool.py -M Significance \
        -m "60,80,100,120,125,130,140,160,180,200,250,300,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500" \
        --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_boundaries.json \
        --setParameters r_ggH=0,r_bbH=0 \
        --redefineSignalPOIs r_bbH \
        -d ${datacarddir}/combined/cmb/ws.root \
        --there -n ".bbH" \
        --job-mode condor \
        --dry-run \
        --task-name bbH_full_cmb_Significance \
        --X-rtd MINIMIZER_analytic \
        --cminDefaultMinimizerStrategy 0 \
        --cminDefaultMinimizerTolerance 0.01 \
        -v 1 \
        | tee -a ${defaultdir}/logs/job_setup_sigind_bbh.txt

    combineTool.py -M Significance \
        -m "60,80,100,120,125,130,140,160,180,200,250,300,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500" \
        --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_boundaries.json \
        --setParameters r_ggH=0,r_bbH=0 \
        --redefineSignalPOIs r_ggH \
        -d ${datacarddir}/combined/cmb/ws.root \
        --there -n ".ggH" \
        --job-mode condor \
        --dry-run \
        --task-name ggH_full_cmb_Significance \
        --X-rtd MINIMIZER_analytic \
        --cminDefaultMinimizerStrategy 0 \
        --cminDefaultMinimizerTolerance 0.01 \
        -v 1 \
        | tee -a ${defaultdir}/logs/job_setup_sigind_ggh.txt

elif [[ $MODE == "submit-sig" ]]; then
    cd ${defaultdir}/significance_ind/condor
    condor_submit condor_ggH_full_cmb_Significance.sub
    condor_submit condor_bbH_full_cmb_Significance.sub

elif [[ $MODE == "collect-sig" ]]; then
    for p in gg bb; do 
        combineTool.py -M CollectLimits ${datacarddir}/combined/cmb/higgsCombine.${p}H.Significance.mH*.root \
            --use-dirs \
            -o ${datacarddir}/combined/cmb/mssm_significance_${p}H.json
    done
fi
