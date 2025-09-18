import napari


if __name__ == '__main__':

    try:
        viewer = napari.Viewer()
    except Exception as e:
        raise RuntimeError(e)