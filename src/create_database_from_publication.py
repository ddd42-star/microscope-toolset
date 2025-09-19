import sys
import asyncio
import chromadb
import os

from usage.pdf_to_markdown import extract_text_from_pdfs, extract_text_from_pdf
from mcp_microscopetoolset.utils import get_user_information
from openai import OpenAI, AsyncOpenAI
from pathlib import Path


async def main():
    # List of arguments giving in the file call
    arguments = sys.argv
    print(arguments)

    if len(arguments) - 1 != 4:
        raise ValueError("Missing arguments.")
    # check if additional keyword were given
    if arguments[1] != "--db" or arguments[3] != "--doc":
        raise ValueError("Missing arguments")

    if arguments[2] == "":
        raise ValueError("Path where to save the vector database is missing!")

    if arguments[4] == "":
        raise ValueError("Path with the pdf(s) is missing!")

    # checks for arguments
    path_for_the_db = arguments[2]
    pdfs_path = arguments[4]

    # Get user information
    system_user_information = get_user_information()

    # Initialize chroma db
    #chroma_client = chromadb.PersistentClient(path=system_user_information['database_path'])
    #pdf_collection = chroma_client.get_or_create_collection(name=system_user_information['pdf_collection_name'])

    # Initialize client and async client
    client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    async_openai = AsyncOpenAI(api_key=os.getenv("OPEnAI_API_KEY"))

    # Fix path
    input_db_dir = os.path.abspath(path_for_the_db).replace("\\", "/")
    input_pdfs_dir = os.path.abspath(pdfs_path).replace("\\", "/")

    if not os.path.isdir(input_db_dir):
        raise ValueError("Please give a value directory path to save the vector database")

    if os.path.isdir(input_pdfs_dir):
        try:
            await extract_text_from_pdfs(input_db_dir, input_pdfs_dir, client_openai, pdf_collection, async_openai)
        except Exception as e:
            return e

    elif os.path.isfile(input_pdfs_dir):
        try:
            await extract_text_from_pdf(input_db_dir, Path(input_pdfs_dir), client_openai, pdf_collection, async_openai)
        except Exception as e:
            return e
    else:
        raise ValueError("Invalid value!")

    return None


if __name__ == "__main__":
    asyncio.run(main())

# FOR TESTING
# Path to DB
# "./new_publication"
# Path to PDF
# Path("C:\\Users\\dario\\OneDrive\\università\\MA\\Thesis\\microscope-toolset\\microscope-toolset\\publications\\publication_1.pdf"))
# Path to PDFs
# "C:\\Users\\dario\\OneDrive\\università\\MA\\Thesis\\microscope-toolset\\microscope-toolset\\test_pipeline_publication")
