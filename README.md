# Chronic Stroke Lesion Segmentation — nnU-Net v2

Pretrained nnU-Net v2 models for automated chronic ischemic stroke lesion segmentation from T1-weighted brain MRI.

The models can be used with the existing NNUNet extension for 3D Slicer, allowing researchers to generate lesion segmentations and visualize the results directly in Slicer.

![SlicerStrokeSegmentator screenshot](SlicerStrokeSegmentator/Resources/Screenshots/StrokeSegmentator.png)

The model repository includes five trained checkpoints, the nnU-Net configuration files, and the custom BCE+Dice trainer required for model loading.

## Features

- Automated chronic stroke lesion segmentation from T1-weighted MRI.
- nnU-Net v2 3D full-resolution architecture.
- Five-fold ensemble inference.
- Custom BCE+Dice trainer.
- Publicly available pretrained model weights.
- Integration with the existing 3D Slicer NNUNet extension.
- Local inference without uploading patient images to a remote server.

## Model configuration

| Parameter | Value |
|---|---|
| Framework | nnU-Net v2 |
| Architecture configuration | 3d_fullres |
| Trainer | nnUNetTrainerBCEDice |
| Plans | nnUNetPlans |
| Target voxel spacing | 1 × 1 × 1 mm³ |
| Patch size | 128 × 128 × 128 |
| Training batch size | 2 |
| Intensity normalization | ZScoreNormalization |
| Ensemble | Five folds (0–4) |
| Input modality | T1-weighted MRI |

The target voxel spacing and normalization are specified in the nnU-Net plans. These preprocessing operations do not replace spatial registration.

## Requirements

- 3D Slicer with the NNUNet extension.
- Compatible nnU-Net v2 installation.
- PyTorch.
- T1-weighted brain MRI prepared consistently with the training data, including registration to MNI152 1 mm space.
- Sufficient system memory and disk space.

Tested environment: 3D Slicer 5.12.4 on Linux, with nnU-Net v2 2.8.1.

Successful inference has been demonstrated in this environment. Windows and macOS compatibility have not yet been independently verified.

## Installation and model setup

### 1. Install the NNUNet extension

Open 3D Slicer, navigate to the Extension Manager, and install the existing NNUNet extension.

Restart Slicer if requested.

### 2. Download the pretrained model

Download the model repository:

https://huggingface.co/parvezamu/stroke-lesion-segmentation

The published model checkpoints are stored under:

```text
Dataset001_StrokeT1w/
  nnUNetTrainer__nnUNetPlans__3d_fullres/
    fold_0/
    fold_1/
    fold_2/
    fold_3/
    fold_4/
```

Each fold contains a `checkpoint_final.pth` file.

The repository also provides the nnU-Net configuration metadata, including `dataset.json` and `plans.json`.

### 3. Install the custom trainer

Download:

[custom_trainer/nnUNetTrainerBCEDice.py](https://huggingface.co/parvezamu/stroke-lesion-segmentation/blob/main/custom_trainer/nnUNetTrainerBCEDice.py)

Copy the trainer into the `nnunetv2/training/nnUNetTrainer/` directory of the Python environment used by the Slicer NNUNet extension.

The custom trainer inherits from the standard nnU-Net trainer and defines the BCE+Dice loss implementation. No additional custom loss file is required.

For the tested Linux installation, the destination was:

```text
Slicer-5.12.4-linux-amd64/
  lib/Python/lib/python3.12/site-packages/
    nnunetv2/training/nnUNetTrainer/
      nnUNetTrainerBCEDice.py
```

The exact location depends on the Slicer installation and operating system.

### 4. Prepare the local model directory

The checkpoint metadata identifies the trainer as `nnUNetTrainerBCEDice`.

After downloading the model, rename the local trainer directory only from:

```text
nnUNetTrainer__nnUNetPlans__3d_fullres
```

to:

```text
nnUNetTrainerBCEDice__nnUNetPlans__3d_fullres
```

Arrange the local model files as follows:

```text
stroke_model/
  Dataset001_StrokeT1w/
    nnUNetTrainerBCEDice__nnUNetPlans__3d_fullres/
      dataset.json
      plans.json
      fold_0/
        checkpoint_final.pth
      fold_1/
        checkpoint_final.pth
      fold_2/
        checkpoint_final.pth
      fold_3/
        checkpoint_final.pth
      fold_4/
        checkpoint_final.pth
```

This is a local installation adjustment. The original Hugging Face checkpoint directory remains unchanged.

### 5. Run inference in 3D Slicer

1. Open 3D Slicer and launch the NNUNet extension.
2. Load a T1-weighted MRI prepared in the required MNI152 space.
3. Configure the local model directory and select the appropriate model.
4. Select the available trained folds for ensemble inference.
5. Run segmentation.
6. Review the resulting lesion segmentation in the Slicer scene.

The predicted segmentation should be visually inspected, particularly for small lesions, atypical anatomy, and registration errors.

## Input image preparation

The model was developed for T1-weighted brain MRI prepared in MNI152 space.

nnU-Net automatically performs configuration-dependent operations such as voxel resampling and Z-score intensity normalization during inference.

However, resampling is not equivalent to anatomical registration.

Users should ensure that their input images have undergone spatial preparation consistent with the training pipeline. Differences in registration, skull stripping, image orientation, field of view, or intensity characteristics may affect segmentation performance.

## Public testing dataset — ATLAS v3.0 collection

A testing collection containing 629 ATLAS cases is available separately:

[Download ATLAS testing collection (Google Drive)](https://drive.google.com/drive/folders/1kgHygdB5PSDqj0ScFCj-nxuHOd5gPvXk?usp=sharing)

The collection is described as containing:

- 329 newly released ATLAS v3.0 cases.
- 300 cases from the former ATLAS v2.0 validation dataset.

These cases are separate from the original 655-case ATLAS v2.0 training dataset used to develop the segmentation model.

The testing collection contains T1-weighted MRI images and corresponding reference lesion masks. Users should verify image geometry, preprocessing, case correspondence, and applicable dataset access and redistribution conditions before use.

### Suggested evaluation metrics

- Dice similarity coefficient (DSC).
- Lesion-wise precision, recall, and F1-score.
- 95th-percentile Hausdorff distance (HD95).
- Lesion volume difference.
- Segmentation failure rate.

These metrics require a separate evaluation procedure and are not automatically calculated by the pretrained model.

### Original dataset source

[ATLAS dataset download portal](https://fcon_1000.projects.nitrc.org/indi/retro/atlas_download.html)

Please acknowledge the original ATLAS dataset publications and comply with their applicable terms.

## Model availability

The pretrained model checkpoints and custom trainer are publicly available:

https://huggingface.co/parvezamu/stroke-lesion-segmentation

The associated research manuscript is currently in preparation.

For research enquiries:

- pahm409@aucklanduni.ac.nz
- parvezamu@gmail.com

## Research and clinical use

For research use only.

This model is not established as a clinically validated diagnostic tool and should not be used independently for clinical diagnosis, treatment decisions, or patient management.

Segmentation performance may vary with MRI acquisition parameters, lesion size, anatomical changes, registration quality, and differences between training and evaluation datasets.

## Citation

Ahmad et al. Manuscript in preparation.

Auckland Bioengineering Institute  
University of Auckland  
New Zealand

Please cite the associated publication when available and acknowledge the original ATLAS dataset publications.

## Acknowledgements

HRC grant 21/144 IMPRESS.

## License

The separate SlicerStrokeSegmentator extension source code is released under the Apache License, Version 2.0, as specified in its source repository. That license should not automatically be assumed to apply to the pretrained model weights.
