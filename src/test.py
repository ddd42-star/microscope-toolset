import napari
from PyQt6.QtWidgets import QPushButton, QToolBar
from PyQt6 import Qt6, QtWidgets
from pymmcore_widgets import ConfigurationWidget

from pymmcore_plus import CMMCorePlus


def main():


    viewer = napari.Viewer()
    dw, mainwindow = viewer.window.add_plugin_dock_widget("napari-micromanager")

    # quick way to access the same core instance as napari-micromanager
    mmc = CMMCorePlus.instance()

    # load config file
    mmc.loadSystemConfiguration()

    #print(mainwindow)

    # do any complicated scripting you want here

    # start napari
    napari.run()


if __name__ == "__main__":
    main()
