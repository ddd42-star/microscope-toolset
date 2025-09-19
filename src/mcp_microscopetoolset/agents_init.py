import os
from openai import OpenAI
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from src.agentsNormal.logger_agent import LoggerAgent
from src.agentsNormal.classify_user_intent import ClassifyAgent
from src.agentsNormal.specialized_agent import DatabaseAgent, SoftwareEngeneeringAgent, StrategyAgent, NoCodingAgent
from src.databases.elasticsearch_db import ElasticSearchDB
from src.local.execute import Execute
from src.mcp_microscopetoolset.microscope_session import MicroscopeSession
from src.mcp_microscopetoolset.utils import logger_database_exists, get_user_information
from src.microscope.microscope_status import MicroscopeStatus
from src.postqrl.connection import DBConnection
from src.postqrl.log_db import LoggerDB
import time


def initialize_agents():
    # Initialize the microscope session object
    microscope_session_object = MicroscopeSession()
    # create the data_dict that will contain the feedback loop information
    # data_dict = microscope_session_object.get_data_dict()

    # Get the information for the user
    system_user_information = get_user_information()

    # start executor and tracking of the microscope status
    executor = Execute(system_user_information['cfg_file'])
    microscope_status = MicroscopeStatus(executor=executor)
    # initialize Logger database and his connection
    db_connection = DBConnection()
    db_log = LoggerDB(db_connection)

    # check if the logger database already exist
    if not logger_database_exists(db_log, system_user_information['log_collection']):
        # it doesn't exist. We create a new one
        db_log.create_collection(system_user_information['log_collection'])
        print(f"A new collection named {system_user_information['log_collection']} has been created.")

    es_client = ElasticSearchDB()
    try_connection = 0

    max_retries = 100
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        print(f"Trying connection to Elasticsearch (attempt {attempt + 1}/{max_retries})...")
        if es_client.is_connected():
            print("Connected to Elasticsearch!")
            break
        time.sleep(retry_delay)
        retry_delay *= 2
        es_client = ElasticSearchDB()
    else:
        raise RuntimeError(
            "Could not connect to Elasticsearch after 100 attempts. Please make sure the server is running.")

    # get relevant information for the db
    pdf_publication = system_user_information['pdf_collection_name']
    micromanager_collection = system_user_information['micromanager_devices_collection']
    api_collection = system_user_information['collection_name']

    # Load the cross-encoder for re-ranking
    # Load model directly
    model_name = "cross-encoder/ms-marco-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)

    # initialize LLM API
    client_openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    # initialize different Agents
    database_agent = DatabaseAgent(client_openai=client_openai, es_client=es_client, pdf_collection=pdf_publication,
                                   micromanager_collection=micromanager_collection, api_collection=api_collection,
                                   db_log=db_log, db_log_collection_name=system_user_information['log_collection'],
                                   tokenizer=tokenizer, model=model)

    software_agent = SoftwareEngeneeringAgent(client_openai=client_openai)

    strategy_agent = StrategyAgent(client_openai=client_openai)

    no_coding_agent = NoCodingAgent(client_openai=client_openai)

    logger_agent = LoggerAgent(client_openai=client_openai)

    classify_agent = ClassifyAgent(client_openai=client_openai)

    return {
        "microscope_session_object": microscope_session_object,
        "executor": executor,
        "microscope_status": microscope_status,
        "database_agent": database_agent,
        "software_agent": software_agent,
        "strategy_agent": strategy_agent,
        "no_coding_agent": no_coding_agent,
        "logger_agent": logger_agent,
        "classify_agent": classify_agent,
        "db_log": db_log,
        "es_client": es_client,
        "client_openai": client_openai,
    }




