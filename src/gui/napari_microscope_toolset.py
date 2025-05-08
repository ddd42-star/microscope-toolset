import napari

# call new napari viewer
viewer = napari.Viewer()

# call the plugins
viewer.window.add_plugin_dock_widget("napari-micromanager")

# start loop for gui interaction
napari.run()



