# import subprocess
# import sys
# import os
# from src.mcp_microscopetoolset.utils import get_user_information
#
# user_information = get_user_information()
#
# fastmcp_server_path = user_information['fastmcp_server_path']
#
# # try to start the server
# try:
#     print("Trying starting MCP server...")
#
#     print(fastmcp_server_path)
#
#     es_process = subprocess.Popen([sys.executable, "-m", fastmcp_server_path], shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#
# # Print the PID for debugging/management
#     print(f"Elasticsearch started with PID: {es_process.pid}")
#     with open("./tmp_fast_es_pid.txt", "w") as f:
#         f.write(str(es_process.pid))
#
#     print(f"Server started with PID: {es_process.pid}")
#
#     print(es_process.stdout.read())
#     print(es_process.stderr.read())
#     es_process.wait()
# except FileNotFoundError:
#     print(f"Error starting elasticsearch: {fastmcp_server_path}")
#     sys.exit(1)
#
# except Exception as e:
#     print(f"Error starting MCP server: {e}", file=sys.stderr)
#     sys.exit(1)

import sys, time, subprocess, logging
from src.mcp_microscopetoolset.utils import get_user_information
from src.databases.elasticsearch_db import ElasticSearchDB
from src.mcp_microscopetoolset.agents_init import initialize_agents
from src.mcp_microscopetoolset.server_setup import create_mcp_server, run_server
from subprocess import Popen, PIPE
import signal

logger = logging.getLogger("FastMCPLauncher")
handler = logging.FileHandler("fastmcp_launch.log")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

elastic_search: Popen[str] = None

def start_elasticsearch():
    global elastic_search
    ui = get_user_information()
    es_home = ui["elastic_search_path_home"]
    if sys.platform.startswith("win"):
        exe = f"{es_home}\\bin\\elasticsearch.bat"
    else:
        exe = f"{es_home}/bin/elasticsearch"
    logger.info(f"Launching Elasticsearch: {exe}")
    elastic_search = subprocess.Popen([exe, "-d", "-p", "pid"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True, text=True)
    logger.info(f"Elasticsearch PID={elastic_search.pid}")

    # with open("./tmp_elastic_es_pid.txt", "w") as f:
    #     f.write(str(elastic_search.pid))
    return elastic_search

def stop_elasticsearch():
    global elastic_search
    if elastic_search is None:
        print("No process running")
        return


    elastic_search.send_signal(signal.SIGTERM)


def wait_for_es(max_wait=60, interval=1):
    es = ElasticSearchDB()
    waited = 0
    while waited < max_wait:
        if es.is_connected():
            logger.info("Elasticsearch is ready!")
            return True
        time.sleep(interval)
        waited += interval
        logger.info(f"Waiting for ES: {waited}/{max_wait}s")
    raise RuntimeError("Elasticsearch did not become ready in time")

def main():
    # 1) Launch ES
    es_proc = start_elasticsearch()

    # 2) Wait until ES actually answers
    try:
        wait_for_es(max_wait=60)
    except Exception as e:
        logger.error(f"ES startup failed: {e}")
        es_proc.terminate()
        sys.exit(1)

    # 3) Initialize agents (will now succeed)
    logger.info("Initializing agents")
    agents = initialize_agents()

    # 4) Create & run FastMCP
    mcp = create_mcp_server(
        database_agent=agents["database_agent"],
        microscope_status=agents["microscope_status"],
        no_coding_agent=agents["no_coding_agent"],
        executor=agents["executor"],
        logger_agent=agents["logger_agent"]
    )
    logger.info("Starting FastMCP server")
    try:
        run_server(mcp)
    except Exception as e:
        logger.exception("FastMCP server crashed")
        sys.exit(1)

if __name__ == "__main__":
    main()


# def main():
#     try:
#         # Wait for Elasticsearch to be ready
#         logger.info("Waiting for Elasticsearch...")
#         wait_for_elasticsearch()
#
#         # Initialize agents
#         logger.info("Initializing agents...")
#         agents = initialize_agents()
#
#         # Create MCP server
#         logger.info("Creating MCP server...")
#         mcp = create_mcp_server(
#             database_agent=agents["database_agent"],
#             microscope_status=agents["microscope_status"],
#             no_coding_agent=agents["no_coding_agent"],
#             executor=agents["executor"],
#             logger_agent=agents["logger_agent"]
#         )
#
#         # Start server
#         logger.info("Starting FastMCP server...")
#         run_server(mcp)
#
#     except Exception as e:
#         logger.exception("FastMCP server failed")
#         sys.exit(1)
#
#
# if __name__ == "__main__":
#     main()
