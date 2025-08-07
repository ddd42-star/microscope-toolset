import asyncio
import json

import chromadb
import pymupdf
import os
import base64
from openai import OpenAI
from openai import AsyncOpenAI
from pydantic import BaseModel
from pathlib import Path
from semantic_text_splitter import MarkdownSplitter

#from usage.prompts import CLEAN_MARKDOWN_TEXT


class ImageToMarkdown(BaseModel):
    title: str = None
    page_number: int = None
    author: str = None
    text: str


def load_file(file_path: Path, vector_db_path: str) -> None:
    """
    Load a PDF file and convert it to a png file.
    """
    # load the pdf file
    doc = pymupdf.open(filename=file_path)
    # create dir for saving images
    images_path = vector_db_path + '/pages_png'

    # create dir with images
    if not os.path.exists(images_path):
        os.makedirs(images_path)

    # convert pdf to an image
    for page in doc:
        pix = page.get_pixmap()
        pix.save(f"{images_path}/page_{page.number:03}.png")

    # close pdf file
    doc.close()

    return None#"The PDFs was converted to a png."

async def encode_image_to_base64(image_path):
    """
    Encode an image to base64
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def image_to_markdown(base64_image):
    """
    Convert an image to a Markdown text. Add metadata of the document like 'title', 'page', 'author', ect
    """
    asynch_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = ("Extract the text and return it in a markdown format."
              "DO NOT include figures and figure descriptions, publication information and pages number, title and author.")
    response = await asynch_client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text",
                     "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{base64_image}",
                        "detail": "high",
                    },
                ],
            }
        ],
        text_format=ImageToMarkdown
    )

    # convert to a json object
    response_json = json.loads(response.output_text)

    return response_json

async def extract_text_from_pdfs(path_for_the_db: str = None, pdfs_path: str = None):
    """
    Given a directory that contains pdf, extract the Markdown text for each of them;
    """
    # check if directory path of the db is given
    if path_for_the_db is None:
        raise ValueError("Please give a valid directory path: None value not allowed!")
    # check path of the pdfs
    if pdfs_path is None:
        raise ValueError("Invalid path of the pdfs directory: None value not allowed!")
    try:
        input_db_dir = os.path.abspath(path_for_the_db).replace("\\", "/")
        input_pdfs_dir = os.path.abspath(pdfs_path).replace("\\", "/")

        if not os.path.isdir(input_db_dir):
            raise ValueError("Please give a value directory path to save the vector database")


        if not os.path.isdir(pdfs_path):
            raise ValueError("Invalid path of the pdfs directory")

        # Get all pdfs from the path
        pdfs_inputs = sorted(Path(input_pdfs_dir).glob("*.pdf"), key=lambda path: path.stem)
        print(pdfs_inputs)
        # iterate throught all the files
        for markdown_file_path in pdfs_inputs:
            print(f"Processing {markdown_file_path}")

            # create folder for each publication
            pdf_file_name = markdown_file_path.name.split('.')[0]
            folder_name = f"{input_db_dir}/{pdf_file_name}"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            # extract text from single pdf
            #markdown_object_single_file = await extract_text_from_pdf(input_db_dir,markdown_file_path)
            print(f"Starting with {pdf_file_name}")
            await extract_text_from_pdf(folder_name, markdown_file_path)
            print(f"Finished with {pdf_file_name}")



    except Exception as e:
        return e

async def extract_text_from_pdf(path_for_the_db: str = None, pdf_path: Path = None):
    """
    This function iterate through all file and extract all the text from the file.
    """
    # check if directory path of the db is given
    if path_for_the_db is None or not os.path.isdir(path_for_the_db):
        raise ValueError("Please give a valid directory path where to save the vector database")
    # path for the vector db
    vector_database = os.path.abspath(path_for_the_db)
    format_vector_database = vector_database.replace("\\", "/")
    # get path name
    pages_folder_vector_database = format_vector_database + '/pages_png'
    markdown_folder_vector_database = format_vector_database + '/pages_markdown'

    # create markdown directory
    if not os.path.exists(markdown_folder_vector_database):
        os.makedirs(markdown_folder_vector_database)

    if not os.path.exists(pages_folder_vector_database):
        os.makedirs(pages_folder_vector_database)

    multimodal_pages = []

    # checks what type of path is: file or directory or unknown
    if os.path.isfile(pdf_path):
        # convert pdf to img PIL
        try:
            load_file(pdf_path, format_vector_database)

            # access image files
            images = sorted(Path(pages_folder_vector_database).iterdir(), key=lambda x: x.stem)
            for image_path in images:
                print(f"Process {image_path}")
                base64_image = await encode_image_to_base64(str(image_path))
                markdown_object = await image_to_markdown(base64_image)
                output_markdown = Path(markdown_folder_vector_database) / f"{image_path.stem}.md"

                # add the Markdown object to the list
                multimodal_pages.append(markdown_object)

                # write raw Markdown text from pages
                with open(output_markdown, 'w', encoding='utf-8') as file:
                    file.write(markdown_object['text'])
                    print(f"Markdown for {image_path.name} saved to {output_markdown}")

                file.close()


            unique_markdown_text = '\n'.join([page['text'] for page in multimodal_pages])#cleaned_markdown_list
            with open(Path(vector_database) / f"{pdf_path.name.split('.')[0]}.md", 'w', encoding='utf-8') as file:
                file.write(unique_markdown_text)

            file.close()

            # create a list with all the chunk, as default will be 5000 charachter
            print("Create chunks list")
            chunks_list = split_markdown(unique_markdown_text, 5000)

            # insert chuncked list into the vector db
            print("Insert chunks into the database")
            insert_chunks_into_collection(pdf_path.name.split('.')[0], chunks_list, pdf_path)

        except Exception as e:
            print(e)
            raise e
    else:
        raise FileNotFoundError("The path to the pdfs doesn't exists!")

def split_markdown(text, max_char = 1000):

    # Maximum number of characters in a chunk
    max_characters = max_char
    # Optionally can also have the splitter not trim whitespace for you
    splitter = MarkdownSplitter(max_characters)

    chunks = splitter.chunks(text)

    return chunks

def get_openai_embeddings(text: str):
    """
    This function return the embedding vector calculated by OpenAI
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(input=text, model="text-embedding-3-small", dimensions=512)

    embedding = response.data[0].embedding
    print(embedding)
    print("Generating embedding")

    return embedding


def insert_chunks_into_collection(file_name: str, chuncked_list: list, pdf_path: Path):
    chroma_client = chromadb.PersistentClient("C:/Users/dario/OneDrive/università/MA/Thesis/microscope-toolset/microscope-toolset/Vectore-store")

    collection_name = chroma_client.get_or_create_collection(name="publication-database")

    for index, chunk in enumerate(chuncked_list):
        print(f"chunk: {index}_{chunk}")
        # create embedding
        embedding_vector = get_openai_embeddings(chunk)

        # create random id
        id_name = f"{file_name}_{index:04}"
        # insert into the collection
        collection_name.upsert(ids=[id_name], metadatas=[{"name": file_name, "path": f"{pdf_path}"}], documents=[chunk], embeddings=[embedding_vector])

    print(f"{file_name} chuncks was inserted into {collection_name}!")

    return None



if __name__ == "__main__":
    #asyncio.run(extract_text_from_pdf(path_for_the_db="./new_publication", pdf_path=Path("C:\\Users\\dario\\OneDrive\\università\\MA\\Thesis\\microscope-toolset\\microscope-toolset\\publications\\publication_1.pdf")))

     asyncio.run(extract_text_from_pdfs(path_for_the_db="./new_publication",
                                        pdfs_path="C:\\Users\\dario\\OneDrive\\università\\MA\\Thesis\\microscope-toolset\\microscope-toolset\\test_pipeline_publication"))