from src.mcp_microscopetoolset.agents_init import initialize_agents
from src.mcp_microscopetoolset.server_setup import create_mcp_server, run_server
from src.databases.elasticsearch_db import ElasticSearchDB
import logging
import time
import subprocess
import os
import sys

logger = logging.getLogger("FastMCPLauncher")
handler = logging.FileHandler("fastmcp_launch.log")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# def wait_for_es(max_wait=60, interval=1):
#     es = ElasticSearchDB()
#     waited = 0
#     while waited < max_wait:
#         logger.info(es)
#         logger.info(es.is_connected())
#         logger.info(f"I waited {waited}")
#         if es.is_connected():
#             logger.info("Elasticsearch is ready!")
#             # close connectio
#             es.close()
#             return True
#         time.sleep(interval)
#         waited += interval
#         logger.info(f"Waiting for ES: {waited}/{max_wait}s")
#     raise RuntimeError("Elasticsearch did not become ready in time")

# 2) Wait until ES actually answers
# try:
#     wait_for_es(max_wait=60)
# except Exception as e:
#     logger.error(f"ES startup failed: {e}")
#     #es_proc.terminate()
#     sys.exit(1)

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