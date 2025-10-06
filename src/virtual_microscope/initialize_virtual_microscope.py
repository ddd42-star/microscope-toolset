from pymmcore_plus import CMMCorePlus

from src.virtual_microscope.microscope_sim import MicroscopeSim
from src.virtual_microscope.pymmcore_camera_sim import SimCameraDevice
from src.virtual_microscope.pymmcore_stage_sim import SimStageDevice
from src.virtual_microscope.pymmcore_state_device_sim import SimStateDevice
from src.virtual_microscope.pymmcore_shutter_sim import SimShutterDevice
from pymmcore_plus.experimental.unicore.core._unicore import UniMMCore
import logging
import sys

#  logger
logger = logging.getLogger("Execute")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("microscope_toolset.log", encoding="utf-8")
fh.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logger.addHandler(fh)



def initialize_virtual_microscope(core: UniMMCore) -> None:

    try:
        # access UniMMCore
        # development python devices
        logger.info("Initialized UniMMCore")
        microscope_simulation = MicroscopeSim()
        logger.info("Initialized MicroscopeSim")

        # -----------------------------------------
        # unload all devices
        core.unloadAllDevices()
        logger.info("Unloaded AllDevices")
        # -----------------------------------------------------
        # load device
        core.loadPyDevice("Camera", SimCameraDevice(core=core, microscope_sim=microscope_simulation))
        logger.info("Load Camera Device")
        core.loadPyDevice("XYStage", SimStageDevice(microscope_sim=microscope_simulation))
        logger.info("Load XYStage Device")
        core.loadPyDevice("LED", SimStateDevice(label="LED",
                                                state_dict={0: "UV", 1: "BLUE", 2: "CYAN", 3: "GREEN", 4: "YELLOW",
                                                            5: "ORANGE", 6: "RED"},
                                                microscope_sim=microscope_simulation))
        logger.info("Load LED Device")
        core.loadPyDevice("Filter Wheel", SimStateDevice(label="Filter Wheel",
                                                         state_dict={0: "Electra1(402/454)", 1: "SCFP2(434/474)",
                                                                     2: "TagGFP2(483/506)", 3: "obeYFP(514/528)",
                                                                     5: "mRFP1-Q667(549/570)", 6: "mScarlet3(569/582)",
                                                                     7: "miRFP670(642/670)"},
                                                         microscope_sim=microscope_simulation))
        logger.info("Load Filter Wheel Device")
        core.loadPyDevice("Shutter", SimShutterDevice())
        logger.info("Shutter Device")
        # ------------------------------------
        # initialize device
        core.initializeDevice("Camera")
        core.initializeDevice("XYStage")
        core.initializeDevice("Filter Wheel")
        core.initializeDevice("LED")
        core.initializeDevice("Shutter")
        logger.info("Initialized Device")

        # ---------------------------
        # Set initial value of some device
        core.setCameraDevice("Camera")
        core.setXYStageDevice("XYStage")
        core.setShutterDevice("Shutter")

        logger.info("Initialization Complete")

    except Exception as e:
        logger.error(f"Error: {e}")
        RuntimeError(f"Error: {e}")