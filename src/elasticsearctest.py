import subprocess
import threading
import napari

from elasticsearch import Elasticsearch

path = "C:\\Users\\dario\\OneDrive\\università\\MA\\Thesis\\microscope-toolset\\microscope-toolset\\elasticsearch-7.17.29"

bin_path = f"{path}\\bin\\elasticsearch.bat"

def stream_logs(proc):
    print(proc)
    for line in proc.stdout:
        print("[ES]", line.strip())

def start_elastic_search_process():
    process = subprocess.Popen(
        bin_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        text=True,
        shell=True
    )

    print(process)

def define_client():

    es = Elasticsearch("http://localhost:4500")

    return es

def run_main():

    es = define_client()

    print(es.info())

def start_thread():
    threading.Thread(target=start_elastic_search_process, daemon=True).start()

    run_main()

if __name__ == "__main__":

    # try:
    #     test_subprocess = subprocess.Popen(bin_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    #
    #     threading.Thread(target=stream_logs, args=(test_subprocess,), daemon=True).start()
    #
    #     for i in range(20):
    #         print(i)
    #
    #     es = Elasticsearch(["http://localhost:4500"])
    #
    #     print(es.info())

    # while True:
    #     test_subprocess = subprocess.Popen(bin_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    #                                        shell=True)
    #
    #     threading.Thread(target=stream_logs, args=(test_subprocess,), daemon=True).start()
    start_thread()

    viewer = napari.Viewer()

    viewer.window.add_plugin_dock_widget(plugin_name="napari-micromanager")

    napari.run()


    # except KeyboardInterrupt:
    #     print("exit!")
    #     test_subprocess.terminate()

