import os, subprocess, shutil, tempfile
import qt, slicer
from slicer.ScriptedLoadableModule import *

MODEL_REPO = "parvezamu/stroke-lesion-segmentation"
MODEL_SUBDIR = "Dataset001_StrokeT1w/nnUNetTrainerImprovedLossCheckpoints__nnUNetPlans__3d_fullres"

class SlicerStrokeSegmentator(ScriptedLoadableModule):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent.title = "Stroke Segmentator"
        self.parent.categories = ["Segmentation"]
        self.parent.dependencies = []
        self.parent.contributors = ["Parvez Ahmad (Auckland Bioengineering Institute)"]
        self.parent.helpText = (
            "Automated chronic ischemic stroke lesion segmentation on T1w MRI. "
            "Input must be registered to MNI152 1mm isotropic space."
        )
        self.parent.acknowledgementText = "HRC grant 21/144 IMPRESS, University of Auckland."

class SlicerStrokeSegmentatorWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        super().setup()
        self.logic = SlicerStrokeSegmentatorLogic()

        formLayout = qt.QFormLayout()

        # Input selector
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.toolTip = "Select T1w MRI registered to MNI152 1mm space"
        formLayout.addRow("Input T1w (MNI152):", self.inputSelector)
        self.layout.addLayout(formLayout)

        # Download button
        self.downloadBtn = qt.QPushButton("Download Model (~1.2 GB, one-time)")
        self.downloadBtn.toolTip = "Downloads model weights from HuggingFace"
        self.downloadBtn.connect("clicked()", self.onDownload)
        self.layout.addWidget(self.downloadBtn)

        # Apply button
        self.applyBtn = qt.QPushButton("Segment Stroke Lesion")
        self.applyBtn.connect("clicked()", self.onApply)
        self.layout.addWidget(self.applyBtn)

        # Status label
        self.statusLabel = qt.QLabel("")
        self.layout.addWidget(self.statusLabel)
        self.layout.addStretch(1)

        # Check if model already downloaded
        if os.path.exists(os.path.join(self.logic.modelDir(), MODEL_SUBDIR)):
            self.statusLabel.setText("Model ready.")
            self.downloadBtn.setText("Model already downloaded")

    def onDownload(self):
        self.statusLabel.setText("Installing dependencies and downloading model...")
        slicer.app.processEvents()
        try:
            self.logic.downloadModel()
            self.statusLabel.setText("Model ready.")
            self.downloadBtn.setText("Model already downloaded")
        except Exception as e:
            self.statusLabel.setText(f"Error: {e}")
            slicer.util.errorDisplay(f"Download failed: {e}")

    def onApply(self):
        node = self.inputSelector.currentNode()
        if not node:
            slicer.util.errorDisplay("Please select an input T1w volume.")
            return
        if not os.path.exists(os.path.join(self.logic.modelDir(), MODEL_SUBDIR)):
            slicer.util.errorDisplay("Model not downloaded. Please click 'Download Model' first.")
            return
        self.statusLabel.setText("Segmenting... (may take 1-2 minutes)")
        slicer.app.processEvents()
        try:
            self.logic.runSegmentation(node)
            self.statusLabel.setText("Segmentation complete.")
        except Exception as e:
            slicer.util.errorDisplay(str(e))
            self.statusLabel.setText("Error — check Python console.")

class SlicerStrokeSegmentatorLogic(ScriptedLoadableModuleLogic):
    def modelDir(self):
        return os.path.join(os.path.expanduser("~"), "stroke_model")

    def installDeps(self):
        import importlib
        for pkg, install_name in [
            ("nnunetv2", "nnunetv2"),
            ("huggingface_hub", "huggingface_hub"),
        ]:
            try:
                importlib.import_module(pkg)
            except ImportError:
                slicer.util.pip_install(install_name)

    def downloadModel(self):
        self.installDeps()
        from huggingface_hub import snapshot_download
        os.makedirs(self.modelDir(), exist_ok=True)
        snapshot_download(
            repo_id=MODEL_REPO,
            repo_type="model",
            local_dir=self.modelDir(),
        )

    def runSegmentation(self, inputNode):
        tmpDir = tempfile.mkdtemp(prefix="slicer_stroke_")
        try:
            inDir = os.path.join(tmpDir, "input")
            outDir = os.path.join(tmpDir, "output")
            os.makedirs(inDir); os.makedirs(outDir)

            # Export input volume
            inPath = os.path.join(inDir, "volume_0000.nii.gz")
            slicer.util.exportNode(inputNode, inPath)

            # Get PythonSlicer path
            pythonPath = os.path.join(
                os.path.dirname(slicer.app.applicationFilePath()),
                "PythonSlicer"
            )

            # Run nnUNet prediction
            env = os.environ.copy()
            env["nnUNet_results"] = self.modelDir()
            cmd = [
                pythonPath, "-m", "nnunetv2.inference.predict_from_raw_data",
                "-i", inDir, "-o", outDir,
                "-d", "Dataset001_StrokeT1w",
                "-tr", "nnUNetTrainerImprovedLossCheckpoints",
                "-p", "nnUNetPlans", "-c", "3d_fullres",
                "-f", "0", "1", "2", "3", "4",
                "-device", "cpu", "--disable_tta",
                "-npp", "1", "-nps", "1",
            ]
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"nnUNet failed:\n{result.stderr[-1000:]}")

            # Load segmentation into Slicer
            outFiles = [f for f in os.listdir(outDir) if f.endswith(".nii.gz")]
            if not outFiles:
                raise RuntimeError("No output file produced by nnUNet.")
            segNode = slicer.util.loadSegmentation(os.path.join(outDir, outFiles[0]))
            segNode.SetName(f"{inputNode.GetName()}_stroke_lesion")
            return segNode
        finally:
            shutil.rmtree(tmpDir, ignore_errors=True)
