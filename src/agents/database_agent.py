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
    
    def retrieve_distances(self, strategy: str):
        # embed the user query
        query_embedded = self.embeds_query(query=strategy)

        # search into the database
        results = self.client_collection.query(query_embeddings=query_embedded, includes=["distances"])

        # Extract relevant chuncks
        #relevant_chuncks = [doc for sublist in results["documents"] for doc in sublist]
        distances = results["distances"][0]


        return distances # [[dis_1m dis_2, dis_3, ...]]



    def verify_strategies(self, strategies: str):


        # retrieve possible informations from the different strategies
        # format the strategies like this: [**-**\n**-**]
        # to choose the best strategies calculate the distance, the nearest one is the best strategy
        best_distance = np.inf
        idx_strategy = 0
        list_of_strategies = strategies.split("**-**")

        for index, strategy in enumerate(list_of_strategies):
            distances = self.retrieve_distances(strategy=strategy)

            smallest_distance = np.min(distances)

            if smallest_distance <= best_distance:
                best_distance = smallest_distance
                idx_strategy = index + 1
        # TODO after look to build ha rank of 1-2-3, so in the end all the strategy will be tried if needed
        if idx_strategy == 0:
            # The three strategies don't works, ask for others
            return None, False



        return list_of_strategies[idx_strategy-1], True
    