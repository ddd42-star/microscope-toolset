from pymmcore_plus.experimental.unicore import XYStageDevice

from .microscope_sim import MicroscopeSim


class SimStageDevice(XYStageDevice):


    def __init__(self, microscope_sim: MicroscopeSim | None = None) -> None:
        super().__init__()
        self._x = 0.0
        self._y = 0.0
        # verify the microscope simulation exists
        if microscope_sim is None:
            raise ValueError("microscope_sim must be provided.")
        self._microscope_sim = microscope_sim

    def home(self) -> None:
        """
        Move to its home position
        """
        self._x = 0.0
        self._y = 0.0

    def stop(self) -> None:
        """
        Stop the movement of the stage
        """
        return

    def set_position_um(self, x: float, y: float) -> None:
        """
        Set the stage position using microns
        """
        self._x = x
        self._y = y
        print("i was run")

    def get_position_um(self) -> tuple[float, float]:
        """
        Return a float representing the current stage position
        """
        # update the camera offset of the simulation
        self.update_camera_offset()

        return self._x, self._y


    def set_origin_x(self) -> None:
        """
        Set the x coordinate of the stage origin
        """
        self._x = 0.0


    def set_origin_y(self) -> None:
        """
        Set the y coordinate of the stage origin
        """
        self._y = 0.0

    def update_camera_offset(self) -> None:
        """
        This method updates the camera offset of the virtual microscope
        """
        self._microscope_sim.camera_offset = (self._x, self._y)
