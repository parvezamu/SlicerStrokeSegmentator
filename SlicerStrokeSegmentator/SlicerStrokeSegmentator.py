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
        self.parent.helpText = "Automated chronic ischemic stroke lesion segmentation on T1w MRI registered to MNI152 1mm space."
        self.parent.acknowledgementText = "HRC grant 21/144 IMPRESS, University of Auckland."

class SlicerStrokeSegmentatorWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        super().setup()
        self.logic = SlicerStrokeSegmentatorLogic()
        formLayout = qt.QFormLayout()
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.toolTip = "Select T1w MRI registered to MNI152 1mm space"
        formLayout.addRow("Input T1w (MNI152):", self.inputSelector)
        self.layout.addLayout(formLayout)
        self.downloadBtn = qt.QPushButton("Download Model (~1.2 GB, one-time)")
        self.downloadBtn.connect("clicked()", self.onDownload)
        self.layout.addWidget(self.downloadBtn)
        self.applyBtn = qt.QPushButton("Segment Stroke Lesion")
        self.applyBtn.connect("clicked()", self.onApply)
        self.layout.addWidget(self.applyBtn)
        self.statusLabel = qt.QLabel("")
        self.layout.addWidget(self.statusLabel)
        self.layout.addStretch(1)
        if os.path.exists(os.path.join(self.logic.modelDir(), MODEL_SUBDIR)):
            self.statusLabel.setText("Model ready.")
            self.downloadBtn.setText("Model already downloaded")

    def onDownload(self):
        self.statusLabel.setText("Downloading model...")
        slicer.app.processEvents()
        try:
            self.logic.downloadModel()
            self.statusLabel.setText("Model ready.")
            self.downloadBtn.setText("Model already downloaded")
        except Exception as e:
            slicer.util.errorDisplay(f"Download failed: {e}")

    def onApply(self):
        node = self.inputSelector.currentNode()
        if not node:
            slicer.util.errorDisplay("Please select an input T1w volume.")
            return
        if not os.path.exists(os.path.join(self.logic.modelDir(), MODEL_SUBDIR)):
            slicer.util.errorDisplay("Model not downloaded. Click 'Download Model' first.")
            return
        self.statusLabel.setText("Segmenting... (1-2 minutes on CPU)")
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
        for pkg in ["nnunetv2", "huggingface_hub"]:
            try: importlib.import_module(pkg)
            except ImportError: slicer.util.pip_install(pkg)

    def downloadModel(self):
        self.installDeps()
        from huggingface_hub import snapshot_download
        os.makedirs(self.modelDir(), exist_ok=True)
        snapshot_download(repo_id=MODEL_REPO, repo_type="model", local_dir=self.modelDir())

    def runSegmentation(self, inputNode):
        tmpDir = tempfile.mkdtemp(prefix="slicer_stroke_")
        try:
            inDir = os.path.join(tmpDir, "input")
            outDir = os.path.join(tmpDir, "output")
            os.makedirs(inDir); os.makedirs(outDir)
            inPath = os.path.join(inDir, "volume_0000.nii.gz")
            slicer.util.exportNode(inputNode, inPath)

            pythonPath = os.path.join(
                os.path.dirname(slicer.app.applicationFilePath()), "PythonSlicer"
            )

            # Use full model path directly — avoids nnUNet_results env var conflicts
            modelPath = os.path.join(self.modelDir(), MODEL_SUBDIR)

            env = os.environ.copy()
            env["nnUNet_results"] = self.modelDir()

            cmd = [
                pythonPath, "-m", "nnunetv2.inference.predict_from_raw_data",
                "-i", inDir, "-o", outDir,
                "-m", modelPath,          # pass full path directly
                "-c", "3d_fullres",
                "-f", "0", "1", "2", "3", "4",
                "-device", "cpu",
                "--disable_tta",
                "-npp", "1", "-nps", "1",
            ]
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"nnUNet failed:\n{result.stderr[-1500:]}")

            outFiles = [f for f in os.listdir(outDir) if f.endswith(".nii.gz")]
            if not outFiles:
                raise RuntimeError("No output file produced.")
            segNode = slicer.util.loadSegmentation(os.path.join(outDir, outFiles[0]))
            segNode.SetName(f"{inputNode.GetName()}_stroke_lesion")
            return segNode
        finally:
            shutil.rmtree(tmpDir, ignore_errors=True)
