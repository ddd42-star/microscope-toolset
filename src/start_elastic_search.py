import subprocess
import os
import time

from mcp_microscopetoolset.utils import get_user_information


def start_elastic_search():
    """
    This function allow to start elastic search in a safe way
    """
    user_information = get_user_information()

    elasticsearch_home = user_information["elasticsearch_home"]

    # build the path depending on the OS
    if os.name == 'nt':
        es_executable = os.path.join(elasticsearch_home, 'bin', 'elasticsearch.bat')
    else:
        es_executable = os.path.join(elasticsearch_home, 'bin', 'elasticsearch')


    # try to start the server

    try:
        print("Starting elastic search...")
        # start the server
        es_process = subprocess.Popen([es_executable], preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # wait the server
        # not sure if is needed...if not just delete
        time.sleep(20)

    except FileNotFoundError:
        return f"Error starting elasticsearch: {es_executable}"

    except Exception as e:
        return f"Error starting elasticsearch: {e}"

