import subprocess
import os
import signal
import sys
from src.databases.elasticsearch_db import ElasticSearchDB
import logging
import time

logger = logging.getLogger("Napari-launcher")
handler = logging.FileHandler("napari_launch.log")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def _start_server(cmd):

    if sys.platform.startswith("win"):
        return subprocess.Popen(cmd, text=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)


def _stop_server(proc):

    if not proc:
        return

    if sys.platform.startswith("win"):
        #proc.send_signal(signal.CTRL_BREAK_EVENT)
        proc.terminate()

    else:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)

    proc.wait()

def wait_for_es(max_wait=60, interval=1):
    es = ElasticSearchDB()
    waited = 0
    while waited < max_wait:
        if es.is_connected():
            logger.info("Elasticsearch is ready!")
            # close es client
            es.close()
            return True
        time.sleep(interval)
        waited += interval
        logger.info(f"Waiting for ES: {waited}/{max_wait}s")
    raise RuntimeError("Elasticsearch did not become ready in time")