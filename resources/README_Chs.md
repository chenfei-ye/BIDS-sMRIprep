

# BIDS-sMRIprep

`BIDS-smriprep` 是针对人脑磁共振3D-T1w结构像的分析流程，是弥散张量成像分析的先决步骤。主要功能包括：
- 去头皮 (*mri_synthstrip*)
- 偏置场矫正 (*N4BiasFieldCorrection*)
- 全脑分割 (*mri_synthseg*)
- 空间标准化 (*MNI space by linear alignment*)
- 脑组织分割 (*5ttgen from MRtrix3*)
- 基于FreeSurfer输出结果的nifti转档
- 质控

数据需要符合[Brain Imaging Data Structure](http://bids.neuroimaging.io/) (BIDS)格式。

[版本历史](CHANGELOG.md)

## 本页内容
* [数据准备](#数据准备)
* [安装](#安装)
* [运行](#运行)
* [参数说明](#参数说明)
* [输出结果](#输出结果)

## 数据准备
数据需要符合[Brain Imaging Data Structure](http://bids.neuroimaging.io/) (BIDS)格式。对于`DICOM`数据文件，建议使用[dcm2bids](https://unfmontreal.github.io/Dcm2Bids)工具进行转档，参考[dcm2bids 转档中文简易使用说明](dcm2bids.md)



## 安装
本地需安装[docker](https://docs.docker.com/engine/install)，具体可参考[步骤](docker_install.md)

### 方式一：拉取镜像
```
docker pull mindsgo-sz-docker.pkg.coding.net/neuroimage_analysis/base/bids-smriprep:latest
docker tag  mindsgo-sz-docker.pkg.coding.net/neuroimage_analysis/base/bids-smriprep:latest  bids-smriprep:latest
```

### 方式二：镜像创建
```
# git clone下载代码仓库
cd BIDS-smriprep
docker build -t bids-smriprep:latest .
```


## 运行
```
docker run -it --rm -v <bids_root>:/bids_dataset bids-smriprep:latest python /run.py /bids_dataset --participant_label 01 02 03 -MNInormalization -fsl_5ttgen -cleanup
```


## 参数说明
####   固定参数说明：
-   `/bids_dataset`: 容器内输入BIDS路径，通过本地路径挂载（-v）


####   可选参数说明：
-   `--participant_label [str]`：指定分析某个或某几个被试。比如`--participant_label 01 03 05`。否则默认按顺序分析所有被试。
-   `--session_label [str]`：指定分析同一个被试对应的某个或某几个session。比如`--session_label 01 03 05`。否则默认按顺序分析所有session。
- `-fsl_5ttgen`：脑组织分割模式[5ttgen](https://mrtrix.readthedocs.io/en/dev/reference/commands/5ttgen.html).
- `-MNInormalization`：MNI空间标准化（线性配准）
- `-freesurfer`: 基于FreeSurfer输出结果的label转档. NOTE: 需要先运行[BIDS-FreeSurfer](https://github.com/chenfei-ye/BIDS-freesurfer) 
- `-v`：版本查看
- `-cleanup`: 移除临时文件


## 输出结果

- 运行日志：`<local_bids_dir>/derivatives/fmripost/runtime.log`
- 去颅骨后的T1w:  `<local_bids_dir>/derivatives/smri_prep/T1w_bet.nii.gz`
- T1w mask:  `<local_bids_dir>/derivatives/smri_prep/T1w_bet_mask.nii.gz`
- 基于synthseg的分割标签:  `<local_bids_dir>/derivatives/smri_prep/T1w_seg.nii.gz`
- 空间标准化后的T1w: `<local_bids_dir>/derivatives/smri_prep/mniWarped.nii.gz`
- 原始空间到MNI空间的转换信息（`ANTs-SyN`）:  `<local_bids_dir>/derivatives/smri_prep/composite_warp_t1_to_mni.nii.gz`
-  MNI空间到原始空间的转换信息（`ANTs-SyN`）:  `<local_bids_dir>/derivatives/smri_prep/composite_warp_mni_to_t1.nii.gz`
-  5tt脑组织分割标签:  `<local_bids_dir>/derivatives/smri_prep/T1w_5tt.nii.gz`
-  desikan图谱的分割标签: `<local_bids_dir>/derivatives/smri_prep/native_parc_desikan.nii.gz`
-  destrieux图谱的分割标签: `<local_bids_dir>/derivatives/smri_prep/native_parc_destrieux.nii.gz`
-  hcpmmp360图谱的分割标签: `<local_bids_dir>/derivatives/smri_prep/native_parc_hcpmmp360.nii.gz`
-  hcpmmp379图谱的分割标签: `<local_bids_dir>/derivatives/smri_prep/native_parc_hcpmmp379.nii.gz`

## Copyright
Copyright © chenfei.ye@foxmail.com
Please make sure that your usage of this code is in compliance with the code license.


