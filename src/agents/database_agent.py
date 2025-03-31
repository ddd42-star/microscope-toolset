from agents.agent import Agent
import chromadb
import numpy as np
from typing import List, Optional

class DatabaseAgent(Agent):

    def __init__(self, client_openai, chroma_client: chromadb.ClientAPI, client_collection: chromadb.Collection):
        super().__init__(client_openai)
        self.chroma_client = chroma_client
        self.client_collection = client_collection

    def embeds_query(self, query) -> np.array:

        response = self.client_openai.embeddings.create(input=query, model="text-embedding-3-small", dimensions=512) # later add model's choice

        embedding = response.data[0].embedding # list of floating values
        print("Generating embedding")

        return np.array(embedding)

    def retrieve_relevant_information(self, query: str) -> List[str]:

        # embed the user query
        query_embedded = self.embeds_query(query=query)

        # search into the database
        results = self.client_collection.query(query_embeddings=query_embedded)

        # Extract relevant chuncks
        relevant_chuncks = [doc for sublist in results["documents"] for doc in sublist]

        print("getting relevant information")

        return relevant_chuncks
    
    def prepare_output(self, relevants_informations: Optional[List[str]] = None) -> str:

        if len(relevants_informations) == 0 or relevants_informations is None:

            return "No relevant information contained into the database."
        
        prompt = """Add prompt"""

        more_relevants_informations = [f"CHUNK {ids}:\n" + relevant_chunk for ids,relevant_chunk in enumerate(relevants_informations)]

        list_of_informations = "\n\n".join(more_relevants_informations)

        response = self.client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages= [
                {
                    "role": "system",
                    "content": "\n\n".join(list_of_informations)
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message
    
    def send_context(self, context: str):

        context_summary = """CONTEXT:\n {context}""".format(context=context)
        
        return context_summary
    

    def search_into_database(self, refactored_query: str) -> str:

        # retrieve relvant informations
        list_of_relevant_informations = self.retrieve_relevant_information(query=refactored_query)

        # Ask to make a summary of the information retrieved
        context_compacted = self.prepare_output(relevants_informations=list_of_relevant_informations)

        # prepare the output for the prompt Agent
        context_summary = self.send_context(context=context_compacted)

        return context_summary

    