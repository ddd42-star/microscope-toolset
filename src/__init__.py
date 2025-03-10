import os
import sys
import chromadb
import textwrap

from openai import OpenAI
from chromadb.utils import embedding_functions
from pypdf import PdfReader
import textwrap

def get_openai_embeddings(text, client):

    response = client.embeddings.create(input=text, model="text-embedding-3-small")

    embedding = response.data[0].embedding
    print("Generating embedding")

    return embedding


# function to query documents
def query_documents(question, client, collection):

    query_embeddings = get_openai_embeddings(question, client)
    
    results = collection.query(query_embeddings=query_embeddings)

    # Extract relevant chuncks
    relevant_chuncks = [doc for sublist in results["documents"] for doc in sublist]

    print("getting relevant information")
    #print(results)

    return relevant_chuncks


# function to generate a response from OpenAI

def generete_response(question, relevant_chuncks, client):

    context = "\n\n".join(relevant_chuncks)

    prompt = (
        "You are scientif assistent for question-asnwering task. Use the following pieces of retrieved context to asnwer the question."
        "If you don't know, say that you don't know. If you don't know ask the user more information. Do this maximum three times and after that"
        "just ask the user to re-formulate the question."
        "\n\nContext:\n" + context + "\n\nQuestion:\n" + question
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role":"system",
                "content": prompt,
            },
            {
                "role":"user",
                "content":question
            },
        ],
    )


    answer = response.choices[0].message

    return answer

def chat_gpt(client, collection):

    # Example query
    # query documents

    # example question and response generation
    #question = "What is the biological function of hGID"

    question = input("Digit your question here: ")

    relevant_chunkcs = query_documents(question, client, collection)

    answer = generete_response(question, relevant_chunkcs, client)

    print("############################################################")
    print(textwrap.fill(answer.content, width=100))
    print("############################################################")




if __name__ == "__main__":

    # get openai key

    openai_key = os.getenv("OPENAI_API_KEY")

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=openai_key,model_name='text-embedding-3-small')

    # initialize chroma client
    # to fix, chroma db doesn' recognise absolut path
    #path = "C:/Users/dario/OneDrive/università/MA/Thesis/microscope-toolset/microscope-toolset/chroma_storage"
    path = "C:/Users/dario/OneDrive/università/MA/Thesis/microscope-toolset/microscope-toolset/chroma_storage"
    chroma_client = chromadb.PersistentClient(path="./chroma_storage")
    collection_name = "publications_qa_collection"
    collection = chroma_client.get_collection(name=collection_name, embedding_function=openai_ef)

    client = OpenAI(api_key=openai_key)


    choice = ""

    while choice != "quit":

        choice = input("Available command:\n Press 'quit' to terminate\n Press 'chat' to start conversation with GPT-4\n\n : ")

        command = choice.lower().strip()

        if command == "quit":
            sys.exit("See you next time!")

        elif command == "chat":
            chat_gpt(client, collection)

        else:
            print("Please choose a valid option ('quit', 'chat')")



