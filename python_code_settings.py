              '
              from pymmcore_plus import CMMCorePlus

                mmc = CMMCorePlus().instance()


                mmc.loadSystemConfiguration('./Jungfrau.cfg')
              
                devices = mmc.getLoadedDevices()
                print(devices)
              '