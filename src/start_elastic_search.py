import subprocess
import os
import time

from src.mcp_microscopetoolset.utils import get_user_information


def start_elastic_search():
    """
    This function allow to start elastic search in a safe way
    """
    user_information = get_user_information()

    elasticsearch_home = user_information["elastic_search_path_home"]

    # build the path depending on the OS
    if os.name == 'nt':
        es_executable = os.path.join(elasticsearch_home, 'bin', 'elasticsearch.bat')
    else:
        es_executable = os.path.join(elasticsearch_home, 'bin', 'elasticsearch')


    # try to start the server

    try:
        print("Starting elastic search...")
        print(es_executable)
        # start the server
        if os.name == 'nt':
            es_process = subprocess.Popen([es_executable, "-d", "-p", "pid"], shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            es_process = subprocess.Popen([es_executable, "-d", "-p", "pid"],shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


        # Print the PID for debugging/management
        print(f"Elasticsearch started with PID: {es_process.pid}")
        with open("./tmp_es_pid.txt", "w") as f:
            f.write(str(es_process.pid))

        #print(es_process.stdout.read())
        es_process.wait()

        # wait the server
        # not sure if is needed...if not just delete
        #time.sleep(100)
        #return es_process.pid

    except FileNotFoundError:
        print(f"Error starting elasticsearch: {es_executable}")
        #return None

    except Exception as e:
        print(f"Error starting elasticsearch: {e}")
        #return None