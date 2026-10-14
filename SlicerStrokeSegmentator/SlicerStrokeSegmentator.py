import os
import shutil
import subprocess
import tempfile

import qt
import slicer

from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleWidget,
    ScriptedLoadableModuleLogic,
)


# ------------------------------------------------------------
# MODEL CONFIGURATION
# ------------------------------------------------------------

DATASET = "Dataset001_StrokeT1w"
TRAINER = "nnUNetTrainerImprovedLossCheckpoints"
PLANS = "nnUNetPlans"
CONFIGURATION = "3d_fullres"

MODEL_SUBDIR = os.path.join(
    DATASET,
    f"{TRAINER}__{PLANS}__{CONFIGURATION}"
)

FOLDS = (0, 1, 2, 3, 4)


# ------------------------------------------------------------
# MODULE
# ------------------------------------------------------------

class SlicerStrokeSegmentator(ScriptedLoadableModule):

    def __init__(self, parent):
        super().__init__(parent)

        self.parent.title = "Stroke Segmentator"
        self.parent.categories = ["Segmentation"]
        self.parent.dependencies = []

        self.parent.contributors = [
            "Parvez Ahmad (Auckland Bioengineering Institute)"
        ]

        self.parent.helpText = (
            "Automated chronic ischemic stroke lesion segmentation "
            "on T1-weighted MRI registered to MNI152 1 mm space. "
            "Model weights are distributed separately to authorised users."
        )


# ------------------------------------------------------------
# USER INTERFACE
# ------------------------------------------------------------

class SlicerStrokeSegmentatorWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        super().setup()

        self.logic = SlicerStrokeSegmentatorLogic()

        formLayout = qt.QFormLayout()

        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = [
            "vtkMRMLScalarVolumeNode"
        ]
        self.inputSelector.setMRMLScene(slicer.mrmlScene)

        formLayout.addRow(
            "Input T1w (MNI152):",
            self.inputSelector
        )

        self.layout.addLayout(formLayout)

        # Local model directory
        self.modelPathButton = qt.QPushButton(
            "Select Local Model Directory"
        )

        self.modelPathButton.toolTip = (
            "Select the nnU-Net results root directory."
        )

        self.modelPathButton.connect(
            "clicked()",
            self.onSelectModelDirectory
        )

        self.layout.addWidget(self.modelPathButton)

        # Segmentation button
        self.applyBtn = qt.QPushButton(
            "Segment Stroke Lesion"
        )

        self.applyBtn.connect(
            "clicked()",
            self.onApply
        )

        self.layout.addWidget(self.applyBtn)

        # Status
        self.statusLabel = qt.QLabel("")
        self.layout.addWidget(self.statusLabel)

        self.layout.addStretch(1)

        # Restore saved directory
        saved = slicer.app.settings().value(
            "SlicerStrokeSegmentator/modelDir",
            ""
        )

        if saved and os.path.isdir(str(saved)):
            self.logic.setModelDir(
                str(saved),
                persist=False
            )

        self.updateModelStatus()

    def updateModelStatus(self):

        if self.logic.modelAvailable():
            self.statusLabel.setText("Model ready.")
        else:
            self.statusLabel.setText(
                "Model not found or incomplete. "
                "Select Local Model Directory."
            )

    def onSelectModelDirectory(self):

        directory = qt.QFileDialog.getExistingDirectory(
            slicer.util.mainWindow(),
            "Select nnU-Net Results Directory",
            self.logic.modelDir()
        )

        if not directory:
            return

        directory = str(directory)

        missing = self.logic.missingModelFiles(directory)

        if missing:
            slicer.util.errorDisplay(
                "Selected directory contains an incomplete model.\n\n"
                + "\n".join(missing)
            )
            return

        self.logic.setModelDir(directory)

        self.updateModelStatus()

    def onApply(self):

        node = self.inputSelector.currentNode()

        if not node:
            slicer.util.errorDisplay(
                "Please select an input T1w MRI."
            )
            return

        if not self.logic.modelAvailable():
            slicer.util.errorDisplay(
                "Model not found or incomplete.\n"
                "Please select the correct local model directory."
            )
            return

        self.applyBtn.enabled = False
        self.statusLabel.setText(
            "Running five-fold stroke lesion segmentation..."
        )

        slicer.app.processEvents()

        try:
            self.logic.runSegmentation(node)

            self.statusLabel.setText(
                "Segmentation complete."
            )

        except Exception as e:
            self.statusLabel.setText(
                "Segmentation failed."
            )
            slicer.util.errorDisplay(str(e))

        finally:
            self.applyBtn.enabled = True


# ------------------------------------------------------------
# SEGMENTATION LOGIC
# ------------------------------------------------------------

class SlicerStrokeSegmentatorLogic(ScriptedLoadableModuleLogic):

    def modelDir(self):

        return getattr(
            self,
            "_modelDir",
            os.path.join(
                os.path.expanduser("~"),
                "stroke_model"
            )
        )

    def setModelDir(self, directory, persist=True):

        self._modelDir = os.path.abspath(directory)

        if persist:
            slicer.app.settings().setValue(
                "SlicerStrokeSegmentator/modelDir",
                self._modelDir
            )

    def modelFolder(self, directory=None):

        root = (
            directory
            if directory is not None
            else self.modelDir()
        )

        return os.path.join(root, MODEL_SUBDIR)

    def missingModelFiles(self, directory=None):

        modelFolder = self.modelFolder(directory)

        required = [
            "dataset.json",
            "plans.json",
        ]

        for fold in FOLDS:
            required.append(
                f"fold_{fold}/checkpoint_final.pth"
            )

        return [
            name
            for name in required
            if not os.path.isfile(
                os.path.join(modelFolder, name)
            )
        ]

    def modelAvailable(self):

        return len(self.missingModelFiles()) == 0

    def runSegmentation(self, inputNode):

        missing = self.missingModelFiles()

        if missing:
            raise RuntimeError(
                "Model files missing:\n"
                + "\n".join(missing)
            )

        tmpDir = tempfile.mkdtemp(
            prefix="slicer_stroke_"
        )

        try:
            inDir = os.path.join(tmpDir, "input")
            outDir = os.path.join(tmpDir, "output")

            os.makedirs(inDir)
            os.makedirs(outDir)

            # Export MRI
            inPath = os.path.join(
                inDir,
                "volume_0000.nii.gz"
            )

            slicer.util.exportNode(
                inputNode,
                inPath
            )

            # Slicer Python executable
            slicerBinDir = os.path.dirname(
                slicer.app.applicationFilePath()
            )

            pythonPath = os.path.join(
                slicerBinDir,
                "PythonSlicer"
            )

            predictScript = os.path.join(
                os.path.dirname(slicerBinDir),
                "lib",
                "Python",
                "bin",
                "nnUNetv2_predict"
            )

            if not os.path.isfile(predictScript):
                raise RuntimeError(
                    "nnUNetv2_predict was not found in Slicer's "
                    "Python environment. Install a compatible "
                    "nnunetv2 package before running inference."
                )

            # Environment
            env = os.environ.copy()

            env["nnUNet_results"] = self.modelDir()

            # IMPORTANT: specify the custom trainer
            cmd = [
                pythonPath,
                predictScript,

                "-i", inDir,
                "-o", outDir,

                "-d", DATASET,

                "-tr", TRAINER,

                "-p", PLANS,

                "-c", CONFIGURATION,

                "-f", "0", "1", "2", "3", "4",

                "-device", "cpu",

                "--disable_tta",

                "-npp", "1",
                "-nps", "1",
            ]

            print("Running nnU-Net prediction:")
            print(" ".join(cmd))

            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise RuntimeError(
                    "nnUNet failed:\n"
                    + result.stderr[-3000:]
                    + "\n"
                    + result.stdout[-1000:]
                )

            # Locate prediction
            outFiles = [
                f for f in os.listdir(outDir)
                if f.endswith(".nii.gz")
            ]

            if not outFiles:
                raise RuntimeError(
                    "nnU-Net produced no segmentation output.\n"
                    + result.stdout[-1000:]
                )

            # Load segmentation into Slicer
            segNode = slicer.util.loadSegmentation(
                os.path.join(outDir, outFiles[0])
            )

            if segNode is None:
                raise RuntimeError(
                    "Slicer could not load the predicted segmentation."
                )

            segNode.SetName(
                f"{inputNode.GetName()}_stroke_lesion"
            )

            return segNode

        finally:
            shutil.rmtree(
                tmpDir,
                ignore_errors=True
            )
