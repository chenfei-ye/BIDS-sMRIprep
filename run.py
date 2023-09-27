# coding:utf8
# Authere: Chenfei 
# update Date:2023/09/03
# function: preprocessing of structural MRI (T1w)
# version: BIDS-smriprep:v4.0


__version__ = 'v4.0'
import os
import sys
import nibabel as nib
import numpy as np
import argparse
import time
import subprocess
import shutil
import glob
import pandas as pd
import datetime
import bids
import utils
from mrtrix3 import run, path
from mrtrix3 import MRtrixError
from loguru import logger
from nilearn.masking import apply_mask
from nilearn.masking import unmask

def runSubject(args, label, smri_path, mrtrix_lut_dir):
    option_5ttgen = args.fsl_5ttgen
    option_mni = args.MNInormalization
    freesurfer = args.freesurfer
    subname = 'sub-' + label
    output_dir = os.path.join(args.bids_dir, 'derivatives', 'smri_prep', subname)
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)


    logger.info('Launching participant-level analysis for subject \'' + label + '\'')

    smri_img = nib.load(smri_path)
    qc_dir = os.path.join(output_dir, 'qc')
    if not os.path.exists(qc_dir):
        os.mkdir(qc_dir)
    
    # raise error is the input file is 2D
    if smri_img.header.get_data_shape()[2] < 80: 
        logger.error("ERROR: the input image is not 3D")
        raise MRtrixError('ERROR: the input image is not 3D')

    # synthseg for t1 parcellation
    prefix = 'T1w'
    vol_csv = os.path.join(output_dir, prefix + '_seg_vol.csv')
    qc_csv = os.path.join(output_dir, prefix + '_seg_qc.csv')
    resample_nii = os.path.join(output_dir, prefix + '_seg_iso.nii.gz')
    output_seg = os.path.join(output_dir, prefix + '_seg.nii.gz')
    if not os.path.exists(output_seg):
        synthseg_cmd = 'mri_synthseg --i ' + smri_path + ' --resample ' + resample_nii + ' --parc --robust --vol ' + vol_csv + ' --qc ' + qc_csv + ' --threads 36 --o ' + output_seg
        run.command(synthseg_cmd)
    # check if resample_nii_path exists. If not, copy one 
    # NOTE: mri_synthseg would not produce resample_nii_path if input is 1mm iso
    if not os.path.exists(resample_nii):
        logger.info('no resampling is needed because input images is already 1mm iso')
        t1_nii = nib.load(smri_path)
        nib.save(t1_nii, resample_nii)
    
    smri_path = resample_nii

    # skull stripping
    smri_ss_path = os.path.join(output_dir, 'T1w' + '_bet.nii.gz') 
    smri_mask_path = os.path.join(output_dir, 'T1w' +'_bet_mask.nii.gz') 
    if os.path.exists(smri_mask_path):
        logger.warning("found results of skull stripping, jump this step")
    else:
        logger.info("start skull stripping")
        run.command('mri_synthstrip -i ' + smri_path + ' -m ' + smri_mask_path + ' -o ' + smri_ss_path)


    # bias correction (output brain with eyes and necks)
    smri_proc_path = os.path.join(output_dir, 'T1w' + '_proc.nii.gz') 
    logger.info('starting N4BiasFieldCorrection')
    if os.path.exists(smri_proc_path):
        logger.warning("found results of N4 bias correction, jump this step")
    else:
        try:
            logger.info("start bias correction")
            run.command('N4BiasFieldCorrection -i ' + smri_path + ' -o ' + smri_proc_path + ' -x ' + smri_mask_path)
        except:
            logger.warning("N4BiasFieldCorrection failed, jump this step")
            shutil.copyfile(smri_path, smri_proc_path)

    # apply mask
    smri_proc_ss_path = os.path.join(output_dir, 'T1w' + '_proc_ss.nii.gz') 
    smri_proc = nib.load(smri_proc_path)
    smri_mask = nib.load(smri_mask_path)
    smri_proc_ss = unmask(apply_mask(smri_proc, smri_mask), smri_mask)
    nib.save(smri_proc_ss, smri_proc_ss_path)

    # brain mask qc
    logger.info('starting qc')
    brain_mask_qc_gif = os.path.join(qc_dir, 'brain_mask_qc.gif')
    run.command('slices ' + smri_proc_path + ' ' + smri_mask_path + ' -o ' + brain_mask_qc_gif)    


    if option_mni:
        MNI152NLin2009cAsym_path = '/template/tpl-MNI152NLin2009cAsym_space-MNI_res-01_T1w_brain.nii.gz'
        MNI152NLin2009cAsym_mask_path = '/template/tpl-MNI152NLin2009cAsym_space-MNI_res-01_brainmask.nii.gz'
        mni1InverseWarp_path = os.path.join(output_dir, 'mni1InverseWarp.nii.gz')
        if os.path.exists(mni1InverseWarp_path):
            logger.info("found results of MNI normalization, jump this step")
        else:
            logger.info("start running MNI normalization")
            run.command('antsRegistrationSyNQuick.sh -d 3 -f ' + MNI152NLin2009cAsym_path + ' -j 1 -m ' + smri_proc_ss_path + 
                    ' -o ' + os.path.join(output_dir, 'mni'))
            run.command('antsApplyTransforms -d 3 -i ' + smri_proc_ss_path + 
                            ' -r ' + MNI152NLin2009cAsym_path + 
                            ' -o [' + os.path.join(output_dir, 'composite_warp_t1_to_mni.nii.gz') + 
                            ',1] -t ' + os.path.join(output_dir, 'mni1Warp.nii.gz') + 
                            ' -t ' + os.path.join(output_dir, 'mni0GenericAffine.mat'))
            run.command('antsApplyTransforms -d 3 -i ' + MNI152NLin2009cAsym_path + 
                            ' -r ' + smri_proc_ss_path + 
                            ' -o [' + os.path.join(output_dir, 'composite_warp_mni_to_t1.nii.gz') + 
                            ',1] -t [' + os.path.join(output_dir, 'mni0GenericAffine.mat') + 
                            ',1] -t ' + os.path.join(output_dir, 'mni1InverseWarp.nii.gz'))
            # MNI spatial normalization qc
            MNInorm_qc_gif = os.path.join(qc_dir, 'MNI_spatial_normalization_qc.gif')
            run.command('slices ' + os.path.join(output_dir, 'mniWarped.nii.gz') + ' ' + MNI152NLin2009cAsym_mask_path + ' -o ' + MNInorm_qc_gif)


  
    if option_5ttgen:
        t1_5tt_path = os.path.join(output_dir, 'T1w_5tt.nii.gz')
        t1_5tt_scratch_dir = os.path.join(output_dir, 'T1w_5tt_dir')
        if os.path.exists(t1_5tt_path):
            logger.info("found results of 5ttgen, jump this step")
        else:
            logger.info("start running 5ttgen")
            if not os.path.exists(t1_5tt_scratch_dir):
                os.mkdir(t1_5tt_scratch_dir)
            run.command('5ttgen fsl ' + smri_proc_ss_path + ' ' + t1_5tt_path + 
                        ' -premasked -nocrop -sgm_amyg_hipp -nocleanup -scratch ' + t1_5tt_scratch_dir)
            # 5tt qc
            T1_5tt_corticalGM_qc_gif = os.path.join(qc_dir, 'T1w_5tt_corticalGM_qc.gif')
            T1_5tt_subcorticalGM_qc_gif = os.path.join(qc_dir, 'T1w_5tt_subcorticalGM_qc.gif')
            T1_5tt_WM_qc_gif = os.path.join(qc_dir, 'T1w_5tt_WM_qc.gif')
            T1_5tt_CSF_qc_gif = os.path.join(qc_dir, 'T1w_5tt_CSF_qc.gif')
            T1_5tt_lesion_qc_gif = os.path.join(qc_dir, 'T1w_5tt_lesion_qc.gif')
            run.command('fslsplit ' + t1_5tt_path + ' ' + os.path.join(output_dir, 'T1w_5tt'))
            run.command('slices ' + smri_proc_path + ' ' + os.path.join(output_dir, 'T1w_5tt0000.nii.gz') + 
              ' -o ' + T1_5tt_corticalGM_qc_gif)
            run.command('slices ' + smri_proc_path + ' ' + os.path.join(output_dir, 'T1w_5tt0001.nii.gz') +
              ' -o ' + T1_5tt_subcorticalGM_qc_gif)
            run.command('slices ' + smri_proc_path + ' ' + os.path.join(output_dir, 'T1w_5tt0002.nii.gz') +
              ' -o ' + T1_5tt_WM_qc_gif)
            run.command('slices ' + smri_proc_path + ' ' + os.path.join(output_dir, 'T1w_5tt0003.nii.gz') +
              ' -o ' + T1_5tt_CSF_qc_gif)
            run.command('slices ' + smri_proc_path + ' ' + os.path.join(output_dir, 'T1w_5tt0004.nii.gz') +
                            ' -o ' + T1_5tt_lesion_qc_gif)

            shutil.rmtree(t1_5tt_scratch_dir)
    
    if freesurfer:
        freesurfer_path = os.path.join(args.bids_dir, 'derivatives', 'freesurfer', 'sub-' + label)
        if not os.path.exists(freesurfer_path):
            logger.error("Failed to detect /derivatives/freesurfer for subject " + label)
        
        parc_image_path = os.path.join(freesurfer_path, 'mri') 

        parc_desikan_native_path = os.path.join(parc_image_path, 'native_desikan.mgz')
        parc_destrieux_native_path = os.path.join(parc_image_path, 'native_destrieux.mgz')
        parc_hcpmmp360_native_path = os.path.join(parc_image_path, 'native_hcpmmp360.mgz')

        # prepare LUT files

        parc_desikan_lut_file = os.path.join(mrtrix_lut_dir, 'FreeSurferColorLUT.txt')
        parc_destrieux_lut_file = parc_desikan_lut_file
        parc_hcpmmp360_lut_file = os.path.join(mrtrix_lut_dir, 'hcpmmp1_original.txt')

        mrtrix_desikan_lut_file = os.path.join(mrtrix_lut_dir, 'fs_default.txt')
        mrtrix_destrieux_lut_file = os.path.join(mrtrix_lut_dir, 'fs_a2009s.txt')
        mrtrix_hcpmmp360_lut_file = os.path.join(mrtrix_lut_dir, 'hcpmmp1_ordered.txt')
        
        # Perform the index conversion
        parc_desikan_native_nii_path = os.path.join(output_dir, 'native_parc_desikan.nii.gz')
        parc_destrieux_native_nii_path = os.path.join(output_dir, 'native_parc_destrieux.nii.gz')
        parc_hcpmmp360_native_nii_path = os.path.join(output_dir, 'native_parc_hcpmmp360.nii.gz')
        parc_hcpmmp379_native_nii_path = os.path.join(output_dir, 'native_parc_hcpmmp379.nii.gz')

        if os.path.exists(parc_hcpmmp379_native_nii_path):
            logger.info("found results of freesurfer post-processing, jump this step")
        else:
            logger.info("start running freesurfer post-processing")
            run.command('labelconvert ' + parc_desikan_native_path + ' ' + parc_desikan_lut_file + ' ' + mrtrix_desikan_lut_file + ' ' + parc_desikan_native_nii_path)
            run.command('labelconvert ' + parc_destrieux_native_path + ' ' + parc_destrieux_lut_file + ' ' + mrtrix_destrieux_lut_file + ' ' + parc_destrieux_native_nii_path)
            run.command('labelconvert ' + parc_hcpmmp360_native_path + ' ' + parc_hcpmmp360_lut_file + ' ' + mrtrix_hcpmmp360_lut_file + ' ' + parc_hcpmmp360_native_nii_path)

            # Fix the sub-cortical grey matter parcellations using FSL FIRST
            run.command('labelsgmfix ' + parc_hcpmmp360_native_nii_path + ' ' + smri_proc_path + ' ' + mrtrix_hcpmmp360_lut_file + ' ' + parc_hcpmmp379_native_nii_path)

    logger.info('Finished participant-level analysis for subject \'' + label + '\'')
    

parser = argparse.ArgumentParser(description='sMRI preprocessing toolkit, including skull stripping, '
                    'synthseg segmentation, MNI normalization, fsl_5ttgen')
parser.add_argument('bids_dir', help='The directory with the input dataset '
                    'formatted according to the BIDS standard.')
parser.add_argument('--participant_label', help='The label(s) of the participant(s) that should be analyzed. The label '
                    'corresponds to sub-<participant_label> from the BIDS spec '
                    '(so it does not include "sub-"). If this parameter is not '
                    'provided all subjects should be analyzed. Multiple '
                    'participants can be specified with a space separated list.',
                    nargs="+")
parser.add_argument('--session_label', help='The label of the session that should be analyzed. The label '
                    'corresponds to ses-<session_label> from the BIDS spec '
                    '(so it does not include "ses-"). If this parameter is not '
                    'provided, all sessions should be analyzed. Multiple '
                    'sessions can be specified with a space separated list.',
                    nargs="+")
parser.add_argument("-fsl_5ttgen", action="store_true", help="run 5ttgen fsl. default: False", default=False)
parser.add_argument("-MNInormalization", action="store_true", help="run MNInormalization to MNI152NLin2009cAsym template. default: False", default=False)
parser.add_argument("-freesurfer", action="store_true", help="generate freesurfer parcellation in nifti format. default: False", default=False)
parser.add_argument('-v', '--version', action='version',
                    version='BIDS-App version {}'.format(__version__))
parser.add_argument("-cleanup", action="store_true",
                    help="remove temp folder after finish",
                    default=False)

start = time.time()

# define input directory
args = parser.parse_args()

# init config
scripts_dir = '/'
mrtrix_lut_dir = os.path.join(scripts_dir, 'mrtrix3', 'labelconvert')

# make output dir
smriprep_dir = os.path.join(args.bids_dir, 'derivatives', 'smri_prep')
path.make_dir(smriprep_dir)

timestamp = str(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
log_path = os.path.join(smriprep_dir, 'runtime_' + timestamp + '.log')
# if os.path.exists(log_path):
#     os.remove(log_path)
logger.add(log_path,backtrace= True, diagnose=True)


# parse bids layout
layout = bids.layout.BIDSLayout(args.bids_dir, derivatives=False, absolute_paths=True)
subjects_to_analyze = []
# only for a subset of subjects
if args.participant_label:
    subjects_to_analyze = args.participant_label
# for all subjects
else:
    subject_dirs = glob.glob(os.path.join(args.bids_dir, "sub-*"))
    subjects_to_analyze = [subject_dir.split("-")[-1] for subject_dir in subject_dirs]
# only use a subset of sessions
if args.session_label:
    session_to_analyze = dict(session=args.session_label)
else:
    session_to_analyze = dict()

subjects_to_analyze.sort()

# running participant level
# find all smri 
for subject_label in subjects_to_analyze:
    smri = [f.path for f in layout.get(subject=subject_label,
                                        suffix='T1w',
                                        extension=["nii.gz", "nii"],
                                        **session_to_analyze)]      
    runSubject(args, subject_label, smri[0], mrtrix_lut_dir)


end = time.time()
running_time = end - start
logger.info('running time: {:.0f}min {:.0f}sec'.format(running_time//60, running_time % 60))





    
