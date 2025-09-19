from .microscope_sim import MicroscopeSim
from .pymmcore_camera_sim import SimCameraDevice
from .pymmcore_stage_sim import SimStageDevice
from .pymmcore_state_device_sim import SimStateDevice
from .pymmcore_shutter_sim import SimShutterDevice
from pymmcore_plus.experimental.unicore.core._unicore import UniMMCore


def initialize_virtual_microscope() -> None:

    try:
        # access UniMMCore
        # development python devices
        core = UniMMCore()
        microscope_simulation = MicroscopeSim()

        # -----------------------------------------
        # unload all devices
        core.unloadAllDevices()
        # -----------------------------------------------------
        # load device
        core.loadPyDevice("Camera", SimCameraDevice(core=core, microscope_sim=microscope_simulation))
        core.loadPyDevice("XYStage", SimStageDevice(microscope_sim=microscope_simulation))
        core.loadPyDevice("LED", SimStateDevice(label="LED",
                                                state_dict={0: "UV", 1: "BLUE", 2: "CYAN", 3: "GREEN", 4: "YELLOW",
                                                            5: "ORANGE", 6: "RED"},
                                                microscope_sim=microscope_simulation))
        core.loadPyDevice("Filter Wheel", SimStateDevice(label="Filter Wheel",
                                                         state_dict={0: "Electra1(402/454)", 1: "SCFP2(434/474)",
                                                                     2: "TagGFP2(483/506)", 3: "obeYFP(514/528)",
                                                                     5: "mRFP1-Q667(549/570)", 6: "mScarlet3(569/582)",
                                                                     7: "miRFP670(642/670)"},
                                                         microscope_sim=microscope_simulation))
        core.loadPyDevice("Shutter", SimShutterDevice())
        # ------------------------------------
        # initialize device
        core.initializeDevice("Camera")
        core.initializeDevice("XYStage")
        core.initializeDevice("Filter Wheel")
        core.initializeDevice("LED")
        core.initializeDevice("Shutter")

        # ---------------------------
        # Set initial value of some device
        core.setCameraDevice("Camera")
        core.setXYStageDevice("XYStage")
        core.setShutterDevice("Shutter")

        print("Initialization Complete")
    except Exception as e:
        RuntimeError(f"Error: {e}")