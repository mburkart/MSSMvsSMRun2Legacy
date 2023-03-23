#!/bin/bash
ulimit -s unlimited

source utils/setup_cmssw.sh

MODE=$1
ERA=$2
CHANNEL=$3
TYPE=$4

[[ -z $1 || -z $2 || -z $3 || -z $4 ]] && echo "[ERROR] Too few parameters given." && exit 1

MASS=1200
[[ -z $5 ]] || MASS=$5

# Derive grouping from given type
case $TYPE in
    per-channel)
        GROUPING="-g htt_et -g htt_mt -g htt_tt -g htt_em"
        ;;

    per-year)
        GROUPING="-g 2016 -g 2017 -g 2018"
        ;;

    *)
        echo "Given type not known"
        exit 1
        ;;
esac

ID=${ERA}-${CHANNEL}
BASEDIR=$(readlink -f analysis_2022_02_28/model-indep_classic_2022-08-08_hSM-in-bg)
taskname="ChannelCompatibilityCheck.Test.${ID}.${TYPE}.mH${MASS}-fitSignal"
DATACARD=${BASEDIR}/datacards_bsm-model-indep/${ERA}/${CHANNEL}/ws.root
NUM_TOYS=5 # multiply x100

# Create directory to hold results
[[ ! -d ${BASEDIR}/compatibility-check/condor ]] && mkdir -p ${BASEDIR}/compatibility-check/condor

case "$MASS" in
    80)
        LOW="-400."
        HIGH="400."
        ;;
    100)
        LOW="-200."
        HIGH="200."
        ;;
    130)
        LOW="-50."
        HIGH="50."
        ;;
    1200)
        LOW="-0.0300"
        HIGH="0.0295"
        ;;
    *)
        LOW="-1.0"
        HIGH="1.0"
        ;;
esac

PARAMETER_RANGES="--setParameterRange r_ggH=${LOW},${HIGH}:r_bbH=${LOW},${HIGH} --rMin=${LOW}"

if [[ "$MODE" == "calculate-test-statistic" ]]; then
    pushd ${BASEDIR}/compatibility-check/

    echo $DATACARD
    ls ${DATACARD}
    combine -M ChannelCompatibilityCheck \
        ${DATACARD} \
        -n .Test.${ID}.${TYPE}.NewCrossingAlgo.v2 \
        --X-rtd MINIMIZER_analytic --X-rtd FITTER_NEW_CROSSING_ALGO --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 --robustFit 1 --stepSize 0.01 \
        --setParameters r_ggH=0,r_bbH=0 --redefineSignalPOIs r_ggH $PARAMETER_RANGES \
        -m $MASS \
        --saveFitResult \
        $GROUPING \
        -v 1 \
        |& tee channel_compatibility_check_${ID}-${TYPE}_mH${MASS}.log

elif [[ "$MODE" == "prepare-toys" ]]; then
    pushd ${BASEDIR}/compatibility-check/condor

    combineTool.py -M ChannelCompatibilityCheck \
        ${DATACARD} \
        --X-rtd MINIMIZER_analytic --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.01 \
        --setParameters r_ggH=3.1607e-03,r_bbH=-1.1196e-04 --redefineSignalPOIs r_ggH $PARAMETER_RANGES \
        -m ${MASS} \
        $GROUPING \
        -n .Test.${ID}.${TYPE} \
        -s 1230:1329:1 -t 10 --toysFrequentist \
        --dry-run --job-mode condor --task-name ${taskname} \
        --runMinos=false \
        -v 1
        # --setParameters r_ggH=0.0031608,r_bbH=-0.00011185 --redefineSignalPOIs r_ggH $PARAMETER_RANGES \
    # Do not run minos for toys as the uncertainties of the parameters are not necessary for the p-values.
    # Test on one toy data seemed to indicate there is no real difference between the two options and there should not be a difference.

elif [[ "$MODE" == "submit" ]]; then
    ############
    # job submission
    ############
    pushd ${BASEDIR}/compatibility-check/condor
    condor_submit condor_${taskname}.sub
    popd

elif [[ "$MODE" == "submit-gc" ]]; then
    ############
    # job submission
    ############
    python scripts/build_gc_job.py \
        --combine-script ${BASEDIR}/compatibility-check/condor/condor_${taskname}.sh \
        --workspace ${DATACARD} \
        --workdir /work/mburkart/workdirs/combine/${taskname} \
        --tag ${taskname} \
        --se-path /storage/gridka-nrg/mburkart/gc_storage/combine/${ID}_$(date +%Y_%m_%d)/${taskname}

    ${CMSSW_BASE}/src/grid-control/go.py /work/mburkart/workdirs/combine/${taskname}/${taskname}.conf -Gc -m 3

elif [[ "$MODE" == "copy-results-gc" ]]; then
    rsync -avhP /storage/gridka-nrg/mburkart/gc_storage/combine/${ID}_$(date +%Y_%m_%d)/${taskname}/output/ ${BASEDIR}/compatibility-check/condor

elif [[ "$MODE" == "collect" ]]; then
    pushd ${BASEDIR}/compatibility-check

    combineTool.py -M CollectGoodnessOfFit --input \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1230.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1231.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1232.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1233.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1234.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1235.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1236.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1237.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1238.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1239.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1240.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1241.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1242.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1243.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1244.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1245.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1246.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1247.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1248.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1249.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1250.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1251.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1252.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1253.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1254.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1255.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1256.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1257.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1258.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1259.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1260.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1261.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1262.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1263.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1264.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1265.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1266.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1267.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1268.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1269.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1270.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1271.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1272.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1273.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1274.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1275.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1276.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1277.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1278.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1279.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1280.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1281.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1282.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1283.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1284.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1285.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1286.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1287.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1288.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1289.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1290.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1291.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1292.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1293.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1294.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1295.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1296.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1297.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1298.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1299.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1300.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1301.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1302.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1303.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1304.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1305.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1306.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1307.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1308.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1309.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1310.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1311.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1312.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1313.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1314.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1315.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1316.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1317.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1318.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1319.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1320.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1321.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1322.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1323.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1324.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1325.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1326.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1327.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1328.root \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root condor/higgsCombine.Test.${ID}.${TYPE}.ChannelCompatibilityCheck.mH${MASS}.1329.root \
        --output ChannelCompatibilityCheck_${ID}-mH${MASS}-${TYPE}.json

    plotGof.py --statistic CCC \
               ChannelCompatibilityCheck_${ID}-mH${MASS}-${TYPE}.json \
               --output ChannelCompatibilityCheck_${ID}-mH${MASS}-${TYPE} \
               --mass ${MASS}.0 \
               --title-right="138 fb^{-1} (13 TeV)" \
               --title-left="m_{#phi} = ${MASS} GeV, ${TYPE}"

    popd

elif [[ "$MODE" == "plot-result" ]]; then

    legend_pos=0
    case $MASS in
        80)
            RANGE="m40,65"
            ;;
        100)
            RANGE="m30,45"
            ;;
        130)
            case $TYPE in
                "per-year")
                    RANGE="m2,12"
                    ;;
                "per-channel")
                    RANGE="m15,20"
                    ;;
            esac
            ;;
        1200)
            # RANGE="m0.012,0.01"
            case $TYPE in
                "per-year")
                    RANGE="m0.002,0.008"
                    ;;
                "per-channel")
                    RANGE="m0.03,0.01"
                    legend_pos=0
                    ;;
            esac
            ;;
        *)
            RANGE="m1.0,0.5"
            ;;
    esac

    source utils/setup_python.sh
    pushd ${BASEDIR}/compatibility-check/

    python ${CMSSW_BASE}/src/CombineHarvester/MSSMvsSMRun2Legacy/plotting/plot_ccc.py \
        higgsCombine.Test.${ID}.${TYPE}.NewCrossingAlgo.v2.ChannelCompatibilityCheck.mH${MASS}.root \
        -o ChannelCompatibilityCheck_FitResults-${ID}-mH${MASS}-${TYPE}-new_style \
        -p r_ggH \
        -r $RANGE \
        --mass $MASS \
        --legend-position $legend_pos \
        --toy-json ChannelCompatibilityCheck_${ID}-mH${MASS}-${TYPE}.json

else
    echo -e "\033[0;31m[ERROR]\033[0m Given mode '$MODE' not known."
    exit 1
fi
