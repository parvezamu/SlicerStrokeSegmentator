# SlicerStrokeSegmentator

3D Slicer extension for automated chronic ischemic stroke lesion segmentation on T1-weighted MRI.

## Requirements
- Input: T1w MRI registered to MNI152 1mm isotropic space (182×218×182 voxels)
- GPU recommended (CPU works but takes ~2 minutes per case)

## Installation
1. Install from 3D Slicer Extension Manager (search "StrokeSegmentator")
2. In the module: click "Download Model" (~1.2GB, one-time)
3. Select your T1w MRI volume and click "Segment Stroke Lesion"

## Model Access
The model weights are currently private pending paper submission. To request early access please contact:

**Parvez Ahmad** — p.ahmad@auckland.ac.nz  
Auckland Bioengineering Institute, University of Auckland

Model weights will be made publicly available upon paper submission.

## Model Details
- Architecture: nnUNet PlainConvUNet with ImprovedLoss
- Training: ATLAS v2.0 + UOA IMPRESS (581 cases, MNI152 1mm)
- Performance: DSC=0.582, LesionF1=0.489 on 624-case multi-site benchmark

## Citation
If you use this extension please cite:

Ahmad et al. (2026) — manuscript in preparation  
Auckland Bioengineering Institute, University of Auckland

## License
Apache 2.0
