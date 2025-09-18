from pymmcore_plus.experimental.unicore import StateDevice
from .microscope_sim import MicroscopeSim

class SimStateDevice(StateDevice):

    def __init__(self, label: str, state_dict: dict[int, str], microscope_sim: MicroscopeSim | None = None) -> None:
        super().__init__(state_dict)
        self._current_state = 0 # default position
        self._current_label = self._state_to_label.get(self._current_state)
        self._name = label

        if microscope_sim is None:
            raise ValueError("microscope simulation not initialized")
        self._microscope_sim = microscope_sim

        # add stateDevice to the simulation
        self.update_microscope_simulation()

    def get_state(self) -> int:
        """
        Return the current state of the filter wheel
        """
        return self._current_state

    def set_state(self, position: int | str) -> None:
        """
        Set the current state of the filter wheel
        """
        if isinstance(position, str):
            position = int(position)

        # if self._current_state != position:
        #     self._current_state = position
        #     # update microscope stateDevice
        #     self.update_microscope_simulation()
        #if self._current_state != position:
        self._current_state = position
        self._current_label = self._state_to_label.get(self._current_state)
        # update microscope stateDevice
        self.update_microscope_simulation()


    def update_microscope_simulation(self) -> None:
        """
        Update the states of the virtual microscope simulation
        """
        # if self._name in self._microscope_sim.state_devices.keys():
        #     print("Used")
        #     self._microscope_sim.state_devices[self._name]["state"] = str(self._current_state)
        #     self._microscope_sim.state_devices[self._name]["label"] = self._current_label

        # self._microscope_sim.state_devices[self._name]["state"] = str(self._current_state)
        # self._microscope_sim.state_devices[self._name]["label"] = self._current_label
        self._microscope_sim.state_devices.update({self._name : {"state": str(self._current_state), "label": self._current_label}})