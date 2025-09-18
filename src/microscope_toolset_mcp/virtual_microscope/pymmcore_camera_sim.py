import time
from collections.abc import Iterator, Mapping, Sequence
from typing import Callable, Optional

from pymmcore_plus import PropertyType

from .pymmcore_slm_sim import SimSLMDevice
import numpy as np
from numpy.typing import DTypeLike
from pymmcore_plus.experimental.unicore import CameraDevice, UniMMCore
from .microscope_sim import MicroscopeSim
import pygame
from pymmcore_plus.experimental.unicore import pymm_property
from PIL import ImageEnhance

class SimCameraDevice(CameraDevice):
    """
    pymmcore_camera_sim.py

    A virtual camera device for pymmcore that generates images using the microscope_sim.py simulation.
    """
    _exposure: float = 10.0
    _brightness: float = 100.0
    _binning: int = 2 # default 2x2
    _mask: Optional[np.ndarray] = None
    _led_channel: str = None
    _filter_wheel_channel: str = None

    def __init__(self, core: UniMMCore | None = None, microscope_sim: MicroscopeSim | None = None) -> None:
        super().__init__()
        if microscope_sim is None:
            raise RuntimeError('microscope_sim must be provided')
        self._sim = microscope_sim
        if core is None:
            print("Note: Provide core to the SimCameraDevice constructor to use SLM features")
        self._core = core
        self._mask = None
        # change limits of binning
        self.set_property_limits("Binning", (0, 20))

    def get_exposure(self) -> float:
        return self._exposure

    def set_exposure(self, exposure: float) -> None:
        self._exposure = exposure

    def shape(self) -> tuple[int, int] | tuple[int, int, int]:
        # Use the simulation's dimensions
        # change it with the viewpoint
        if self._sim.n_channel == 2:
            return self._sim.viewport_height, self._sim.viewport_width
        else:
            return self._sim.viewport_height, self._sim.viewport_width, self._sim.n_channel

    def dtype(self) -> DTypeLike:
        return np.uint8

    def set_mask(self, mask: Optional[np.ndarray]) -> None:
        self._mask = mask

    def start_sequence(
        self,
        n: int | None,
        get_buffer: Callable[[Sequence[int], DTypeLike], np.ndarray],
    ) -> Iterator[Mapping]:

        count = 0
        while n is None or count < n:
            time.sleep(self._exposure / 1000.0)
            # Try to read the mask from the core SLM device, if available.
            mask = None
            if self._core is not None:
                try:
                    slm_device = self._core.getSLMDevice()
                    if slm_device:
                        mask = self._core.getSLMImage(slm_device)
                        if mask is not None:
                            mask = mask.astype(bool)
                        else:
                            print("SLM device returned no image, using default mask.")
                    else:
                        print("No SLM device found in core.")
                except Exception as e:
                    print(f"Error getting SLM image: {e}")
            if mask is None:
                mask = np.zeros((self._sim.viewport_height, self._sim.viewport_width), dtype=bool)
            self._mask = mask
            # checking the stage position
            #stage_position = self._get_current_xy_stage_position()
            # update the stage/camera offset
            #self._sim.camera_offset = np.array([stage_position[0], stage_position[1]])
            # For the moment use one of the function to get the microscope frame
            #surf = self._sim.get_frame(self._mask)
            #surf = self._sim.get_frame_random_gray()
            surf = self._sim.snap_frame(mask, self._brightness, self._exposure)
            # create buffer
            buf = get_buffer(self.shape(), self.dtype())
            # apply intensity and exposure time
            #surf = self._sim.apply_intensity(surface=surf, intensity=self._brightness, exposure=self._exposure)
            # convert to array
            #arr = pygame.surfarray.array3d(surf)
            # Convert to grayscale (take one channel)
            #arr = arr[..., 0].astype(np.uint8)
            #buf[:] = arr.T  # Transpose to (height, width)
            #print(buf)
            buf[:] = surf
            #print("image before ", buf)
            #buf[:] = self._apply_current_brightness(brightness=self._brightness, current_image=buf) ## apply current values of brightness
            #print("image after ", buf)
            yield {
                "data": buf,
                "timestamp": time.time()
                }
            # update count
            count += 1
# self._seq_buffer.finalize_slot(
#                 {
#                     **base_meta,
#                     **cam_meta,
#                     KW.Metadata_TimeInCore: received,
#                     KW.Metadata_ImageNumber: str(img_number),
#                     KW.Elapsed_Time_ms: f"{elapsed_ms:.2f}",
#                 }
#             )


    # define property brightness
    @pymm_property(
        limits=(0.0,100.0),
        sequence_max_length=10000,
        name="brightness",
        property_type=PropertyType.Float
    )
    def brightness(self) -> float:
        """
        Get the brightness of the virtual camera.
        """
        return self._brightness

    # setter methods
    @brightness.setter
    def brightness(self, value: float) -> None:
        """
        Send the values to the virtual hardware to update the brightness.
        """
        self._brightness = value

    @brightness.sequence_loader
    def load_position_sequence(self, sequence: Sequence[float]) -> None:
        print(f"Loading position sequence: {sequence}")

    @brightness.sequence_starter
    def start_position_sequence(self) -> None:
        print("Starting position sequence")

    def get_binning(self) -> int:
        """
        Return the current binning of the virtual camera.
        """
        return self._binning

    def set_binning(self, binning: int) -> None:
        """
        Set the current binning of the virtual camera.
        """
        self._binning = binning




def test():
    # Example usage
    core = UniMMCore()
    core.loadPyDevice("Camera", SimCameraDevice())
    core.initializeDevice("Camera")
    core.setCameraDevice("Camera")
    core.setExposure(42)

    try:
        from pymmcore_widgets import ExposureWidget, ImagePreview, LiveButton, SnapButton
        from qtpy.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget

        app = QApplication([])

        window = QWidget()
        window.setWindowTitle("Sim Microscope Camera Example")
        layout = QVBoxLayout(window)

        top = QHBoxLayout()
        top.addWidget(SnapButton(mmcore=core))
        top.addWidget(LiveButton(mmcore=core))
        top.addWidget(ExposureWidget(mmcore=core))
        layout.addLayout(top)
        layout.addWidget(ImagePreview(mmcore=core))
        window.setLayout(layout)
        window.resize(800, 600)
        window.show()
        app.exec()
    except Exception:
        print("run `pip install pymmcore-widgets[image] PyQt6` to run the GUI example")
        core.snapImage()
        image = core.getImage()
        print("Image shape:", image.shape)
        print("Image dtype:", image.dtype)
        print("Image data:", image)