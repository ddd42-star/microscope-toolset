from src.prompts.strategyAgentPrompt import STRATEGY_NEW
from .base_agent import BaseAgent, OpenAI
import json
from .structuredOutput import ClassificationAgentOutput, NoCodingAgentOutput, SoftwareAgentOutput, StrategyAgentOutput,RephraseOutput, ExtractKeywordOutput
from src.prompts.mainAgentPrompt import CLASSIFY_INTENT_NEW, ANSWER_PROMPT
from src.prompts.softwareEngineeringPrompt import SOFTWARE_AGENT_NEW, SOFTWARE_AGENT_RETRY_NEW
from src.databases.elasticsearch_db import ElasticSearchDB
from src.postqrl.log_db import LoggerDB
import torch
from typing import Any, List
import logging
import sys

#  logger
logger = logging.getLogger("Specialized Agent")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)
fh = logging.FileHandler("microscope_toolset.log", encoding="utf-8")
fh.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logger.addHandler(fh)


class ClassifyAgent(BaseAgent):
    """
    Classifier agent for the user input
    """
    def classify_user_intent(self, context):

        prompt = CLASSIFY_INTENT_NEW.format(relevant_inputs=json.dumps(context))

        history = [{"role": "system", "content": prompt},
                   {"role": "user", "content": context['user_query']}] #+ context['conversation']
        error_description = "Failed to classify intent"

        return self.call_agent(model="gpt-4.1-mini",input_user=history, error_string=error_description, output_format=ClassificationAgentOutput)


class NoCodingAgent(BaseAgent):
    """
    to add
    """

    def no_coding_answer(self, context):
        prompt = ANSWER_PROMPT.format(additional_data=context)

        history = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": context["user_query"]
            }
        ]

        error_description = "Failed to answer a non coding question"

        return self.call_agent(model="gpt-4.1-mini",input_user=history, error_string=error_description, output_format=NoCodingAgentOutput)


class SoftwareEngeneeringAgent(BaseAgent):

    def generate_code(self, context):
        print(context)
        prompt = SOFTWARE_AGENT_NEW.format(relevant_context=json.dumps(context))

        history = [{"role": "system", "content": prompt}, {"role": "user", "content": context["user_query"]}] #+ context[
            #"conversation"]

        error_description = "Failed to generate code"

        return self.call_agent(model="gpt-4.1-mini",input_user=history, error_string=error_description, output_format=SoftwareAgentOutput)

    def fix_code(self, context):

        prompt = SOFTWARE_AGENT_RETRY_NEW.format(relevant_context=json.dumps(context))
        history = [{"role": "system", "content": prompt}, {"role": "user", "content": context["user_query"]}] + context[
            "conversation"]

        error_description = "Failed to fix code"

        return self.call_agent(model="gpt-4.1-mini",input_user=history, error_string=error_description, output_format=SoftwareAgentOutput)


class StrategyAgent(BaseAgent):

    def generate_strategy(self, context):
        #print(context)
        prompt = STRATEGY_NEW.format(relevant_context=json.dumps(context))
        print(prompt)

        history = [{"role": "system", "content": prompt}, {"role": "user", "content": context["user_query"]}] #+ context[
            #"conversation"]
        print(history)
        error_description = "Failed to generate strategy"

        return self.call_agent(model="gpt-4.1-mini",input_user=history, error_string=error_description, output_format=StrategyAgentOutput)

    def revise_strategy(self, context):

        prompt = STRATEGY_NEW.format(relevant_context=json.dumps(context))

        history = [{"role": "system", "content": prompt}, {"role": "user", "content": context["user_query"]}] + context[
            "conversation"]

        error_description = "Failed to revise strategy"

        return self.call_agent(model="gpt-4.1-mini",input_user=history, error_string=error_description, output_format=StrategyAgentOutput)

class DatabaseAgent(BaseAgent):

    # add missing variable
    def __init__(self, client_openai: OpenAI,es_client: ElasticSearchDB, pdf_collection: str,
                 micromanager_collection: str, api_collection: str, db_log: LoggerDB, db_log_collection_name: str,
                 tokenizer: Any, model: Any):
        super().__init__(client_openai)
        self.es_client = es_client
        self.pdf_collection = pdf_collection
        self.micromanager_collection = micromanager_collection
        self.api_collection = api_collection
        self.db_log = db_log
        self.db_log_name = db_log_collection_name
        self.tokenizer = tokenizer
        self.model = model

    def _embeds_query(self, query: str) -> List[float]:

        response = self.client_openai.embeddings.create(input=query, model="text-embedding-3-small",
                                                        dimensions=512)  # later add model's choice

        embedding = response.data[0].embedding  # list of floating values
        print("Generating embedding")

        return embedding

    def _retrieve_relevant_information(self, query: str):

        try:
            # embed the user query
            query_embedded = self._embeds_query(query=query)

            # search into the database for chroma
            # results = self.client_collection.query(query_embeddings=query_embedded, n_results=25)
            # search into the db of Elasticsearch
            # 1. search into the api collection
            api_docs_result = self.es_client.hybrid_search(index_name=self.api_collection, query=query,
                                                           query_vector=query_embedded,
                                                           keyword_to_search_for_bm25="contextualize_text")
            # 2. search into pdf collection
            pdf_docs_results = self.es_client.hybrid_search(index_name=self.pdf_collection, query=query,
                                                            query_vector=query_embedded,
                                                            keyword_to_search_for_bm25="content")
            # 3. search into micromanager devices
            micromanager_docs_results = self.es_client.hybrid_search(index_name=self.micromanager_collection, query=query,
                                                                     query_vector=query_embedded,
                                                                     keyword_to_search_for_bm25="content")
            # now extract list of object for reranking
            list_api_docs_result = [{
                "type": result["_source"]["type"],
                "name": result["_source"]["name"],
                "signature": result["_source"]["signature"],
                "description": result["_source"]["description"],
                "filename": result["_source"]["filename"],
                "contextualize_text": result["_source"]["contextualize_text"],
                "score": result["_score"]
            }
                for result in api_docs_result["hits"]["hits"]
            ]
            list_pdf_docs_results = [{
                "content": result["_source"]["content"],
                "chunk_id": result["_source"]["chunk_id"],
                "filename": result["_source"]["filename"],
                "score": result["_score"]
            }
                for result in pdf_docs_results["hits"]["hits"]
            ]
            list_micromanager_docs_results = [{
                "doc_id": result["_source"]["doc_id"],
                "content": result["_source"]["content"],
                "chunk_id": result["_source"]["chunk_id"],
                "filename": result["_source"]["filename"],
                "score": result["_score"]
            }
                for result in micromanager_docs_results["hits"]["hits"]
            ]
            # sort list of results
            list_api_docs_result = sorted(list_api_docs_result, key=lambda x: x["score"], reverse=True)
            list_micromanager_docs_results = sorted(list_micromanager_docs_results, key=lambda x: x["score"], reverse=True)
            list_pdf_docs_results = sorted(list_pdf_docs_results, key=lambda x: x["score"], reverse=True)

            # merge all result into a single list
            merged_list = []
            # iterate through the first list
            merged_list = self._rerank_and_add_to_list(merged_list=merged_list, partial_result_list=list_api_docs_result,
                                                      keyword_field="contextualize_text", query=query)
            # iterate through the second list
            merged_list = self._rerank_and_add_to_list(merged_list=merged_list, partial_result_list=list_pdf_docs_results,
                                                      keyword_field="content", query=query)
            # iterate through the last list
            merged_list = self._rerank_and_add_to_list(merged_list=merged_list,
                                                      partial_result_list=list_micromanager_docs_results,
                                                      keyword_field="content", query=query)
            #print(merged_list)
            # sort the list descending, from higher score through lower
            sorted_merged_list = sorted(merged_list, key=lambda x: x["score"], reverse=True)
            #print(sorted_merged_list)

            # Just keep first 25 results
            results = sorted_merged_list[:24]
            #print(results)

            # search into the database for the log
            log_result = self.db_log.query_by_vector(collection_name=self.db_log_name, vector=query_embedded, k=5)
            # print(log_result)
            if log_result is None:
                log_result = []

            relevant_information = [json.dumps(chunk) for chunk in results]

            # log_relevant_chunks
            log_chunks = [
                json.dumps({
                    "prompt": log_result[i]['prompt'],
                    "output": log_result[i]['output'],
                    "feedback": log_result[i]['feedback'],
                    "category": log_result[i]['category']
                })
                for i in range(len(log_result))
            ]

            # print(log_chunks)
            print("getting relevant information")

            joined_chunks = [*relevant_information, *log_chunks]

            return joined_chunks
        except Exception as e:
            return [f"Error getting relevant information from databases: {str(e)}"]

    def _retrieve_api_information(self, reformulated_query: str) -> list | str:
        try:
            # embed the user query
            query_embedded = self._embeds_query(query=reformulated_query)

            # search into the db of Elasticsearch
            # 1. search into the api collection
            api_docs_result = self.es_client.hybrid_search(index_name=self.api_collection, query=reformulated_query,
                                                           query_vector=query_embedded,
                                                           keyword_to_search_for_bm25="contextualize_text")

            # now extract list of object for reranking
            list_api_docs_result = [{
                "type": result["_source"]["type"],
                "name": result["_source"]["name"],
                "signature": result["_source"]["signature"],
                "description": result["_source"]["description"],
                "filename": result["_source"]["filename"],
                "contextualize_text": result["_source"]["contextualize_text"],
                "score": result["_score"]
            }
                for result in api_docs_result["hits"]["hits"]]

            # sort list of results
            sorted_list_api_docs_result = sorted(list_api_docs_result, key=lambda x: x["score"], reverse=True)

            # merge all result into a single list
            merged_list = []
            # iterate through the first list
            merged_list = self._rerank_and_add_to_list(merged_list=merged_list,
                                                       partial_result_list=sorted_list_api_docs_result,
                                                       keyword_field="contextualize_text", query=reformulated_query)
            # sort the list descending, from higher score through lower
            sorted_merged_list = sorted(merged_list, key=lambda x: x["score"], reverse=True)


            return sorted_merged_list[0:24]

        except Exception as e:
            return f"Error retrieving information from databases: {str(e)}"

    def _retrieve_api_micromanager_information(self, reformulated_query: str) -> list | str:
        try:
            # embed the user query
            query_embedded = self._embeds_query(query=reformulated_query)

            # 3. search into micromanager devices
            micromanager_docs_results = self.es_client.hybrid_search(index_name=self.micromanager_collection,
                                                                     query=reformulated_query,
                                                                     query_vector=query_embedded,
                                                                     keyword_to_search_for_bm25="content")

            list_micromanager_docs_results = [{
                "doc_id": result["_source"]["doc_id"],
                "content": result["_source"]["content"],
                "chunk_id": result["_source"]["chunk_id"],
                "filename": result["_source"]["filename"],
                "score": result["_score"]
            }
                for result in micromanager_docs_results["hits"]["hits"]
            ]

            # sort list of results
            sorted_list_micromanager_docs_results = sorted(list_micromanager_docs_results, key=lambda x: x["score"],
                                                    reverse=True)

            merged_list = []

            # iterate through the last list
            merged_list = self._rerank_and_add_to_list(merged_list=merged_list,
                                                       partial_result_list=sorted_list_micromanager_docs_results,
                                                       keyword_field="content", query=reformulated_query)

            sorted_merged_list = sorted(merged_list, key=lambda x: x["score"], reverse=True)

            return sorted_merged_list[0:24]

        except Exception as e:
            return f"Error retrieving information from databases: {str(e)}"

    def _retrieve_pdfs_information(self, reformulated_query: str) -> list | str:
        try:
            # embed the user query
            query_embedded = self._embeds_query(query=reformulated_query)

            # 2. search into pdf collection
            pdf_docs_results = self.es_client.hybrid_search(index_name=self.pdf_collection, query=reformulated_query,
                                                            query_vector=query_embedded,
                                                            keyword_to_search_for_bm25="content")

            list_pdf_docs_results = [{
                "content": result["_source"]["content"],
                "chunk_id": result["_source"]["chunk_id"],
                "filename": result["_source"]["filename"],
                "score": result["_score"]
            }
                for result in pdf_docs_results["hits"]["hits"]
            ]

            # sort list of results
            sorted_list_pdf_docs_results = sorted(list_pdf_docs_results, key=lambda x: x["score"], reverse=True)

            merged_list = []

            # iterate through the second list
            merged_list = self._rerank_and_add_to_list(merged_list=merged_list,
                                                       partial_result_list=sorted_list_pdf_docs_results,
                                                       keyword_field="content", query=reformulated_query)

            sorted_merged_list = sorted(merged_list, key=lambda x: x["score"], reverse=True)

            return sorted_merged_list[0:24]

        except Exception as e:
            return f"Error retrieving information from databases: {str(e)}"

    def api_pymmcore_context(self, query: str, reformulated_query: str) -> dict[str, ...]:

        # retrieve relevant information from the api
        list_api_docs_result = self._retrieve_api_information(reformulated_query)

        if list_api_docs_result is None or len(list_api_docs_result) == 0:
            return {
                "user_query": query,
                "reformulated_query": reformulated_query,
                "context": "No relevant information were retrieved"
            }
        logger.info({
            "tool": "pymmcore_api_database",
            "user_query": query,
            "reformulated_query": reformulated_query,
            "context": list_api_docs_result
        })
        return {
            "user_query": query,
            "reformulated_query": reformulated_query,
            "context": list_api_docs_result
        }

    def devices_micromanager_context(self, query: str, reformulated_query: str) -> dict[str, ...]:

        # retrieve relevant information from the micromanager device database
        list_devices_micromanager_result = self._retrieve_api_micromanager_information(reformulated_query)

        if list_devices_micromanager_result is None or len(list_devices_micromanager_result) == 0:
            return {
                "user_query": query,
                "reformulated_query": reformulated_query,
                "context": "No relevant information were retrieved"
            }
        logger.info({
            "tool": "micromanager_device_database",
            "user_query": query,
            "reformulated_query": reformulated_query,
            "context": list_devices_micromanager_result
        })
        return {
            "user_query": query,
            "reformulated_query": reformulated_query,
            "context": list_devices_micromanager_result
        }

    def pdf_publication_context(self, query: str, reformulated_query: str) -> dict[str, ...]:

        # retrieve relevant information from the publication of scientific articles
        list_pdfs_result = self._retrieve_pdfs_information(reformulated_query)

        if list_pdfs_result is None or len(list_pdfs_result) == 0:
            return {
                "user_query": query,
                "reformulated_query": reformulated_query,
                "context": "No relevant information were retrieved"
            }
        logger.info({
            "tool": "pdfs_publication_database",
            "user_query": query,
            "reformulated_query": reformulated_query,
            "context": list_pdfs_result
        })
        return {
            "user_query": query,
            "reformulated_query": reformulated_query,
            "context": list_pdfs_result
        }

    def look_for_context(self, query: str) -> str:

        # retrieve relevant information
        list_of_relevant_information = self._retrieve_relevant_information(query=query)

        if len(list_of_relevant_information) == 0 or list_of_relevant_information is None:
            return "No relevant information contained into the database."

        more_relevant_information = [f"CHUNK {ids}:\n" + relevant_chunk for ids, relevant_chunk in
                                       enumerate(list_of_relevant_information)]

        list_of_information = "\n\n".join(more_relevant_information)

        return list_of_information

    def add_log(self, data) -> None:
        #logger = logging.getLogger(__name__)
        # if ["prompt", "output", "feedback", "category"] not in data.keys():
        #    logger.error("missing data")

        # insert the feedback from the user inside the database
        vector = self._embeds_query(data['prompt'])
        # print(vector)
        self.db_log.insert(self.db_log_name, data, embeddings=vector)

    def rephrase_query(self, query: str):

        prompt = """
                    Given the user question, rephrase and expand it to help you do better answering. Maintain all information in the original question.
                    This new reformulated query will be used to retrieve the most relevant information from our database.
                    """
        history = [{"role": "system", "content": prompt}, {"role": "user", "content": query}]

        error_description = "Failed to rephrase the original query"

        return self.call_agent(model="gpt-4.1-mini",input_user=history, error_string=error_description, output_format=RephraseOutput)

    def split_query_in_keyword(self, query: str):

        prompt = """
                    From the user query extract keywords to use for searching into the BM25 database
                    Extract only the key technical terms, endpoint names, methods, and parameter names
                    from the following query. 
                    Return them as a list of string, no explanations.
                    """
        history = [{"role": "system", "content": prompt}, {"role": "user", "content": query}]

        error_description = "Failed to extract keywords from the original query"

        return self.call_agent(model="gpt-4.1-mini",input_user=history, error_string=error_description, output_format=ExtractKeywordOutput)


    def _rerank(self, query: str, chunk: str):
        """
        This function rerank the result obtained from hybrid search
        """
        try:
            print("Starting rerank")
            inputs = self.tokenizer(query, chunk, return_tensors="pt", truncation=True, max_length=512)
            self.model.eval()
            with torch.no_grad():
                scores = self.model(**inputs).logits

            return scores.item()

        except Exception as e:
            return f"Failed to rerank query: {e}"

    def _rerank_and_add_to_list(self, merged_list: list, partial_result_list: list, keyword_field: str, query: str):
        """
        This function iterate through the partial list and rerank the result giving a new score
        """
        try:
            for hit in partial_result_list:
                score = self._rerank(query, hit[keyword_field])
                # add the score to the json object
                hit["score"] = score
                merged_list.append(hit)

            return merged_list

        except Exception as e:
            return f"Failed to rerank query: {e}"