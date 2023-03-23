#!/bin/bash
# This script produces prefit shapes from existing datacards
# to show the effect of uncertainty variations on the full
# mTtot distribution.
# It assumes that the datacards and workspaces for the extraction
# of prefit shapes has already been performed for the model-independent
# analysis.

MODE=$1

defaultdir=$(readlink -f analysis_2022_02_28/model-indep_classic_2022-08-08_hSM-in-bg)
datacarddir=${defaultdir}/datacards_bsm-model-indep

get_shift () {
    [ "$#" != 2 ] && exit
    case $1 in
        nominal)
            echo ""
            ;;
        up)
            echo "scale_embed_met_mt_$2=1,scale_embed_met_$2=1"
            ;;
        down)
            echo "scale_embed_met_mt_$2=-1,scale_embed_met_$2=-1"
            ;;
        *)
            exit
    esac
}

sig_freeze="MH=1200,r_ggH=0.003,r_bbH=0.001"

case $MODE in
    prefit-shapes)
        #####################
        # Extract prefit shapes.
        #####################
        # for era in 2016 2017 2018; do
        for var in nominal up down; do
            if [[ $var == "nominal" ]]; then
                freeze=$sig_freeze
            else
                freeze="$sig_freeze,$(get_shift $var $era)"
            fi
            for era in 2017; do
                echo "${datacarddir}/${era}/htt_em_2_*/combined.txt.cmb"
                prefit_postfit_shapes_parallel.py --datacard_pattern "${datacarddir}/${era}/htt_em_2_*/combined.txt.cmb" \
                                                  --workspace_name ws.root \
                                                  --output_name prefit_shapes_emb_met_${var}.root \
                                                  --parallel 8 |& tee ${defaultdir}/logs/extract_model_independent_shapes-combined-emb_met_${var}.log
                prefit_postfit_shapes_parallel.py --datacard_pattern "${datacarddir}/${era}/htt_*_3*/combined.txt.cmb" \
                                                  --workspace_name ws.root \
                                                  --freeze_arguments "--freeze ${sig_freeze}" \
                                                  --output_name prefit_shapes_emb_met_${var}.root \
                                                  --parallel 8 |& tee -a ${defaultdir}/logs/extract_model_independent_shapes-combined-emb_met_${var}.log
                prefit_postfit_shapes_parallel.py --datacard_pattern "${datacarddir}/${era}/htt_mt_3*/combined.txt.cmb" \
                                                  --workspace_name ws.root \
                                                  --freeze_arguments "--freeze ${freeze}" \
                                                  --output_name prefit_shapes_emb_met_${var}.root \
                                                  --parallel 8 |& tee -a ${defaultdir}/logs/extract_model_independent_shapes-combined-emb_met_${var}.log
            done
            hadd -f ${datacarddir}/combined/cmb/prefit_shapes_emb_met_${var}.root ${datacarddir}/201?/htt_*/prefit_shapes_emb_met_${var}.root |& tee -a ${defaultdir}/logs/extract_model_independent_shapes-combined-emb_met_${var}.log
        done
        ;;

    do-plots)
        source utils/setup_cvmfs_sft.sh
        source utils/setup_python.sh

        CMB=1
        cmb_flag=""
        [[ "$CMB" == "1" ]] && cmb_flag="--combine-backgrounds"

        output=${datacarddir}/plots-variations-emb_met/
        if [[ ! -d "${output}" ]]
        then
            mkdir ${output}
        fi
        channels=(mt)

        for OPTION in "" "--png"
        do
            ./plotting/plot_shapes_mssm_variations.py \
                                           -i ${datacarddir}/combined/cmb/prefit_shapes_emb_met_nominal.root \
                                           -c ${channels[@]} \
                                           -e 2017 \
                                           $OPTION \
                                           --fake-factor \
                                           --embedding \
                                           --normalize-by-bin-width \
                                           -o ${output} \
                                           --up-variation ${datacarddir}/combined/cmb/prefit_shapes_emb_met_up.root \
                                           --down-variation ${datacarddir}/combined/cmb/prefit_shapes_emb_met_down.root \
                                           ${cmb_flag} \
                                           --x-range 0,200 \
                                           --name "CMS_scale_met_emb" \
                                           --linear
                                           # --blinded \
        done
        ;;

    *)
        echo "\033[0;31m[ERROR]\033[0m Given mode $MODE not implemented..."
        exit 1
esac
