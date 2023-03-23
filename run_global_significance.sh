#!/bin/bash
# Script to run global p-value and significance calculation
# Note: Toy generation with GenerateOnly in usual way starts from b-only best-fit
#       if loaded workspace is used the fit is a s+b and the toys are drawn from this
#       distribution with POIs set to the values given by `--setParameters`
ulimit -s unlimited

mode=$1

defaultdir="${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/analysis_2022_02_28/model-indep_classic_2022-08-08_hSM-in-bg/"
datacarddir=${defaultdir}/datacards_bsm-model-indep

# Calculation of p-values is performed in two steps
# 1) Generation of postfit-toys
# In the following command a range of seeds should be specified, also condor arguments are missing

# 2) Extract signifcance of each toy for all considered mass points

[[ ! -d ${defaultdir}/global_significance/condor ]] && mkdir -p ${defaultdir}/global_significance/condor 
case $mode in
    "create-snapshot")
        pushd ${defaultdir}/global_significance/condor
        combineTool.py \
            -M MultiDimFit \
            -m 500 \
            --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_boundaries.json \
            --setParameters r_ggH=0,r_bbH=0 \
            -d ${datacarddir}/combined/cmb/ws.root \
            --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 \
            --saveWorkspace \
            -n ".snapshot.for.toys" \
            -v 2 \
            |& tee ${defaultdir}/logs/create_workspace_snapshot_global_significance.log
            ;;

    "prepare-toy-creation")
        pushd ${defaultdir}/global_significance/condor
        combineTool.py \
            -M GenerateOnly \
            -m 500 \
            -d ${datacarddir}/combined/cmb/ws.root \
            --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_boundaries.json \
            --setParameters r_ggH=0,r_bbH=0 \
            --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 \
            -s 0:399:1 -t 20 --saveToys --toysFrequentist \
            -n ".toys" \
            --task-name global_pvalue_toys \
            --job-mode "condor"  --dry-run \
            -v 1
            # -s 0:499:1 -t 20 --saveToys --toysFrequentist \
            # --snapshotName MultiDimFit --bypassFrequentistFit \
            # -d higgsCombine.snapshot.for.toys.MultiDimFit.mH500.root \
            ;;

    "submit-toy-creation")
        pushd ${defaultdir}/global_significance/condor
        condor_submit condor_global_pvalue_toys.sub
        ;;

    "prepare-fits")
        pushd ${defaultdir}/global_significance/condor
        for i in {0..399}; do
            combineTool.py \
                -M Significance \
                -m "60,80,100,120,125,130,140,160,180,200,250,300,350,400,450,500,600,700,800,900,1000,1200,1400,1600,1800,2000,2300,2600,2900,3200,3500" \
                --boundlist ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/input/mssm_boundaries.json \
                --setParameters r_ggH=0,r_bbH=0 --redefineSignalPOIs r_ggH \
                -d ${datacarddir}/combined/cmb/ws.root \
                --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 \
                --cminFallbackAlgo Minuit2,Simplex,0:0.1 \
                -t 20 -s $i --toysFile higgsCombine.toys.GenerateOnly.mH500.${i}.root --toysFrequentist \
                -n ".ggH.${i}" \
                --task-name ggH_full_cmb_Significance_global_${i} \
                --job-mode condor --dry-run \
                -v 1 
        done
        ;;

    "run-fits")
        pushd ${defaultdir}/global_significance/condor
        for i in {300..399}; do
            condor_submit condor_ggH_full_cmb_Significance_global_${i}.sub
        done
        ;;

    "calculate-pvalue")
        source /cvmfs/sft.cern.ch/lcg/views/LCG_101/x86_64-centos7-gcc10-opt/setup.sh
        python scripts/get_global_pval.py -i ${defaultdir} --verbose
        ;;

    *)
        echo "[ERROR] Given mode not known. Exiting..."
        exit 1
        ;;
esac
