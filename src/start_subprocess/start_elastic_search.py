import subprocess
import os
import sys
from src.mcp_microscopetoolset.utils import get_user_information

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
    with open("./tmp_elastic_es_pid.txt", "w") as f:
        f.write(str(es_process.pid))

    #print(es_process.stdout.read())
    es_process.wait()

except FileNotFoundError:
    print(f"Error starting elasticsearch: {es_executable}")
    sys.exit(1)

except Exception as e:
    print(f"Failed to start Elasticsearch: {e}", file=sys.stderr)
    sys.exit(1)

