import chromadb
import numpy as np
from typing import List, Optional
from openai import OpenAI
from prompts.databaseAgentPrompt import DATABASE_PROMPT


class DatabaseAgent:

    def __init__(self, client_openai: OpenAI, chroma_client: chromadb.ClientAPI, client_collection: chromadb.Collection):
        self.client_openai = client_openai
        self.chroma_client = chroma_client
        self.client_collection = client_collection

    def embeds_query(self, query) -> np.array:

        response = self.client_openai.embeddings.create(input=query, model="text-embedding-3-small",
                                                        dimensions=512)  # later add model's choice

        embedding = response.data[0].embedding  # list of floating values
        print("Generating embedding")

        return np.array(embedding)

    def retrieve_relevant_information(self, query: str) -> List[str]:

        # embed the user query
        query_embedded = self.embeds_query(query=query)

        # search into the database
        results = self.client_collection.query(query_embeddings=query_embedded, n_results=10)

        # Extract relevant chuncks
        SIMILARITY_THREASHOLD = 0.80

        # result
        relevant_chuncks = [f"\n **Function:** {results['metadatas'][0][i]['function_name']}\n **Signature:** {results['metadatas'][0][i]['signature']}\n **Description:** {results['metadatas'][0][i]['description']}\n **Doc Snippet:**\n{results['documents'][0][i]}" for i in range(len(results["documents"][0]))]
        #relevant_chuncks = [doc for sublist in results["documents"] for doc in sublist]
        #relevant_chuncks = []
        #for index, doc in enumerate(results["documents"][0]):
        #    # transform distances into a similsrity score
        #    score = self.similarity_score(results["distances"][0][index])
        #    print(score)

        #    if score >= SIMILARITY_THREASHOLD:
        #        relevant_chuncks.append(doc)
        print("getting relevant information")

        return relevant_chuncks

    def prepare_output(self, refactored_query: str, relevants_informations: Optional[List[str]] = None) -> str:

        if len(relevants_informations) == 0 or relevants_informations is None:
            return "No relevant information contained into the database."

        more_relevants_informations = [f"CHUNK {ids}:\n" + relevant_chunk for ids, relevant_chunk in
                                       enumerate(relevants_informations)]

        list_of_informations = "\n\n".join(more_relevants_informations)

        prompt = DATABASE_PROMPT.format(context=list_of_informations)

        response = self.client_openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": refactored_query
                },
            ],
        )

        return response.choices[0].message.content

    def send_context(self, context: str):

        context_summary = """CONTEXT:\n {context}""".format(context=context)

        return context_summary

    def search_into_database(self, refactored_query: str) -> str:

        # retrieve relvant informations
        list_of_relevant_informations = self.retrieve_relevant_information(query=refactored_query)

        # Ask to make a summary of the information retrieved
        context_compacted = self.prepare_output(refactored_query=refactored_query, relevants_informations=list_of_relevant_informations)

        # prepare the output for the prompt Agent
        context_summary = self.send_context(context=context_compacted)

        return context_summary

    def look_for_context(self, query: str) -> str:

        # retrieve relvant informations
        list_of_relevant_informations = self.retrieve_relevant_information(query=query)

        if len(list_of_relevant_informations) == 0 or list_of_relevant_informations is None:
            return "No relevant information contained into the database."

        more_relevants_informations = [f"CHUNK {ids}:\n" + relevant_chunk for ids, relevant_chunk in
                                       enumerate(list_of_relevant_informations)]

        list_of_informations = "\n\n".join(more_relevants_informations)

        return  list_of_informations


    def retrieve_distances(self, strategy: str):
        # embed the user query
        query_embedded = self.embeds_query(query=strategy)

        # search into the database
        results = self.client_collection.query(query_embeddings=query_embedded, n_results=50)

        distances = results["distances"][0]

        return distances  # [dis_1m dis_2, dis_3, ...]

    def verify_strategies(self, strategies: str):

        # retrieve possible informations from the different strategies
        # format the strategies like this: [**-**\n**-**]
        # to choose the best strategies calculate the distance, the nearest one is the best strategy
        best_distance = np.inf # L2 distance goes from 0 to inf
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

        return list_of_strategies[idx_strategy - 1], True


    def similarity_score(self, distance: float) -> float:
        # transforming distance in range (0,1)
        score = 1/(1 + distance)

        return score
