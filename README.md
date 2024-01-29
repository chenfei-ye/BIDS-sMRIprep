

# BIDS-sMRIprep

`BIDS-smriprep` is developed to perform structural brain MRI data (3D-T1w) pre-process, aiming to support following diffusion MRI analysis. Main functions include:
- skull stripping(*mri_synthstrip*)
- bias correction(*N4BiasFieldCorrection*)
- anatomical parcellation(*mri_synthseg*)
- spatial normalization (*MNI space by linear alignment*)
- five tissue segmentation (*5ttgen from MRtrix3*)
- label conversion from FreeSurfer derivatives
- [cortical similarity networks (MIND)](https://doi.org/10.1038/s41593-023-01376-7) creation
- quality control

The input data should be arranged according to [BIDS format](https://bids.neuroimaging.io/). Input image modalities must be 3D-T1w data. 

[BIDS-sMRIprep 中文说明](resources/README_Chs.md)

Check bids-smriprep version history in [Change Log](resources/CHANGELOG.md)

## Contents
* [Install](#Install)
* [Running](#running)
* [Input Argument](#input-argument)
* [Output Explanation](#output-explanation)
* [Sources](#sources)

## Install
### install by pulling (recommend)
```
docker pull mindsgo-sz-docker.pkg.coding.net/neuroimage_analysis/base/bids-smriprep:latest
docker tag  mindsgo-sz-docker.pkg.coding.net/neuroimage_analysis/base/bids-smriprep:latest  bids-smriprep:latest
```

### or install by docker build
```
cd BIDS-smriprep
docker build -t bids-smriprep:latest .
```

## Running
### default running
```
docker run -it --rm -v <bids_root>:/bids_dataset bids-smriprep:latest python /run.py /bids_dataset --participant_label 01 02 03 -MNInormalization -fsl_5ttgen -cleanup
```

### MIND network running
use [BIDS-freesurfer](https://github.com/chenfei-ye/BIDS-freesurfer) for freesurfer data preprocessing
```
docker run -it --rm --entrypoint python -v /input_bids_directory:/bids_dataset -v /input_bids_directory/derivatives/freesurfer:/outputs -v <localpath>/freesurfer_license.txt:/license.txt  bids-freesurfer:latest /run_fs_batch.py /bids_dataset /outputs participant --skip_bids_validator
```
mapping to hcpmmp and Schaefer atlas
```
docker run -it --rm --entrypoint python -v /input_bids_directory:/bids_dataset -v /<localpath>/freesurfer_license.txt:/license.txt bids-freesurfer:latest /surf_conv.py /bids_dataset participant 
```
creat MIND network
```
docker run -it --rm -v <bids_root>:/bids_dataset bids-smriprep:latest python /run.py /bids_dataset --participant_label 01 02 03 -freesurfer -mind aparc HCPMMP1 schaefer100 schaefer200 schaefer400 -cleanup
```

## Input Argument
####   positional argument:
-   `/bids_dataset`: The root folder of a BIDS valid dataset (sub-XX folders should be found at the top level in this folder).

####   optional argument:
-   `--participant_label [str]`：A space delimited list of participant identifiers or a single identifier (the sub- prefix can be removed)
-   `--session_label [str]`：A space delimited list of session identifiers or a single identifier (the ses- prefix can be removed)
- `-fsl_5ttgen`：run [5ttgen](https://mrtrix.readthedocs.io/en/dev/reference/commands/5ttgen.html) mode.
- `-MNInormalization`：perform MNI normalization using ANTs-SyN.
- `-freesurfer`: perform label conversion from FreeSurfer derivatives. NOTE: `hcpmmp_conv.py` from [BIDS-FreeSurfer](https://github.com/chenfei-ye/BIDS-freesurfer) must be ran before this command. 
- `-mind ["aparc", "aparc.a2009s", "aparc.DKTatlas", "HCPMMP1"]`: perform [MIND network](https://doi.org/10.1038/s41593-023-01376-7) creation. `aparc`  means desikan atlas, `aparc.a2009s`  means destrieux atlas, `aparc.DKTatlas`  means DKT atlas, `HCPMMP1`  means Glasser360 atlas, `schaefer100`  = Schaefer atlas with 100 nodes, `schaefer200`  = Schaefer atlas with 200 nodes, `schaefer400`  = Schaefer atlas with 400 nodes. NOTE: `surf_conv.py` from [BIDS-FreeSurfer](https://github.com/chenfei-ye/BIDS-freesurfer) must be ran before this command. Additionally, optional argument `-freesurfer` should also be specified. 
- `-v`：check version 
- `-cleanup`: remove temporary files.


## Output explanation
-   log:  `<local_bids_dir>/derivatives/smri_prep/sub-XX/runtime.log`
-   skull stripped brain:  `<local_bids_dir>/derivatives/smri_prep/sub-XX/T1w_bet.nii.gz`
-   brain mask:  `<local_bids_dir>/derivatives/smri_prep/sub-XX/T1w_bet_mask.nii.gz`
-   synthseg parcellation label:  `<local_bids_dir>/derivatives/smri_prep/sub-XX/T1w_seg.nii.gz`
-   normalized T1w image: `<local_bids_dir>/derivatives/smri_prep/sub-XX/mniWarped.nii.gz`
-   warpping map from native to MNI space:  `<local_bids_dir>/derivatives/smri_prep/sub-XX/composite_warp_t1_to_mni.nii.gz`
-   warpping map from MNI to native space:  `<local_bids_dir>/derivatives/smri_prep/sub-XX/composite_warp_mni_to_t1.nii.gz`
-  5tt label image:  `<local_bids_dir>/derivatives/smri_prep/sub-XX/T1w_5tt.nii.gz`
-  desikan parcellation label: `<local_bids_dir>/derivatives/smri_prep/sub-XX/native_parc_desikan.nii.gz`
-  destrieux parcellation label: `<local_bids_dir>/derivatives/smri_prep/sub-XX/native_parc_destrieux.nii.gz`
-  hcpmmp360 parcellation label: `<local_bids_dir>/derivatives/smri_prep/sub-XX/native_parc_hcpmmp360.nii.gz`
-  hcpmmp379 parcellation label: `<local_bids_dir>/derivatives/smri_prep/sub-XX/native_parc_hcpmmp379.nii.gz`
- MIND network: `<local_bids_dir>/derivatives/smri_prep/sub-XX/MIND_network_XXX.csv`

## Sources
- `SynthStrip`: a skull-stripping tool that extracts brain voxels from a landscape of image types, [check details](https://surfer.nmr.mgh.harvard.edu/docs/synthstrip/)
- `SynthSeg`: a deep learning tool for segmentation of brain scans of any contrast and resolution, [check details](https://github.com/BBillot/SynthSeg)
- `desikan parcellation`: Desikan-Killiany Atlas included inside FreeSurfer
- `destrieux parcellation`: Destrieux Atlas included inside FreeSurfer
- `hcpmmp 360 parcellation`  : HCP-MMP1.0 parcellation by  [Glasser et al. (Nature)](http://www.nature.com/nature/journal/v536/n7615/full/nature18933.html). See details  [here](https://cjneurolab.org/2016/11/22/hcp-mmp1-0-volumetric-nifti-masks-in-native-structural-space/).
- `hcpmmp 379 parcellation`  : `hcpmmp 360 parcellation` + 19 subcortical parcel labels.

## Copyright
Copyright © chenfei.ye@foxmail.com
Please make sure that your usage of this code is in compliance with the code license.


