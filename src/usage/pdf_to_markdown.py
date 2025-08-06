import asyncio
import json

import pymupdf
import pymupdf4llm
import os
import base64
from openai import OpenAI
from openai import AsyncOpenAI
from pydantic import BaseModel
from pathlib import Path

#from usage.prompts import CLEAN_MARKDOWN_TEXT


class ImageToMarkdown(BaseModel):
    title: str = None
    page_number: int = None
    author: str = None
    text: str
class MarkdownText(BaseModel):
    title: str
    author: str
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
        pix.save(f"{images_path}/page-%i.png" % page.number)

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
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    asynch_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = ("Extract the markdown text output from this page in a PDF using formatting to match the structure of the page as close as you can get. Only output the markdown and nothing else. Do not explain the output, just return it. Do not use a single # for a heading. All headings will start with ## or ### or ####. Convert tables to markdown tables. Describe charts as best you can. DO NOT return in a codeblock. Just return the raw text in markdown format."
              "Add the metadata required. Some field will be changed only once because are different images of the same PDF.")
    response = await asynch_client.responses.parse(
        model="gpt-4.1",
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
        output_db_dirt = "to add"

        if not os.path.isdir(input_db_dir):
            raise ValueError("Please give a value directory path to save the vector database")


        if not os.path.isdir(pdfs_path):
            raise ValueError("Invalid path of the pdfs directory")

        # Get all pdfs from the path
        pdfs_inputs = sorted(Path(input_pdfs_dir).glob("*.pdf"), key=lambda path: path.stem)
        # iterate throught all the files
        for markdown_file_path in pdfs_inputs:
            print(f"Processing {markdown_file_path}")
            # extract text from single pdf
            #markdown_object_single_file = await extract_text_from_pdf(input_db_dir,markdown_file_path)
            #print(markdown_file_path)
            #print(markdown_file_path.name)
            #print(markdown_object_single_file)
            print(markdown_file_path.absolute())



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
    pymupdf4llm_folder_vector_database = format_vector_database + '/pymupdf4llm_markdown'

    # create markdown directory
    if not os.path.exists(markdown_folder_vector_database):
        os.makedirs(markdown_folder_vector_database)
    # create other dir
    if not os.path.exists(pymupdf4llm_folder_vector_database):
        os.makedirs(pymupdf4llm_folder_vector_database)
    multimodal_pages = []
    pymupdf4llm_pages = []

    # checks what type of path is: file or directory or unknown
    if os.path.isfile(pdf_path):
        # get file name
        file_name = os.path.abspath(pdf_path).replace("\\", "/")
        # convert pdf to img PIL
        try:
            load_file(pdf_path, format_vector_database)
        except Exception as e:
            raise e
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

        # # extract the markdown text using pymupdf4llm
        # # extract Markdown text using pymupdf4llm
        # docs = pymupdf.open(pdf_path)
        # for page in docs:
        #     print(f"Process {page}")
        #     page_text = pymupdf4llm.to_markdown(doc=pdf_path, pages=[page.number])
        #     # write the file
        #     Path(f"{pymupdf4llm_folder_vector_database}/page-%i.md" % page.number).write_bytes(page_text.encode())
        #     # add to the list
        #     infos = {
        #         "page": page.number,
        #         "text": page_text
        #     }
        #     pymupdf4llm_pages.append(infos)
        cleaned_markdown_list = []
        # # Use both markdown object to create the final one
        for i, _ in enumerate(multimodal_pages):
            cleaned_markdown_text = await clean_markdown(multimodal_pages[i], pymupdf4llm_pages)
            cleaned_markdown_list.append(cleaned_markdown_text)
            with open(f"{pymupdf4llm_folder_vector_database}/page-{i}.md", 'w', encoding='utf-8') as file:
                file.write(cleaned_markdown_text['text'])
            file.close()
        #cleaned_markdown_text = await clean_markdown(multimodal_pages, pymupdf4llm_pages)

        # create unique Markdown doc
        unique_markdown_text = ''.join([page['text'] for page in cleaned_markdown_list])
        with open(Path(vector_database) / f"{pdf_path.name.split('.')[0]}.md", 'w', encoding='utf-8') as file:
            file.write(unique_markdown_text)
            #file.write(cleaned_markdown_text['text'])

        file.close()

    else:
        raise FileNotFoundError("The path to the pdfs doesn't exists!")


async def clean_markdown(multimodal_object: dict, pymupdf_object: list):
    asynch_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    #prompt = CLEAN_MARKDOWN_TEXT
    #sections = '\n'.join([page['text'] for page in multimodal_object])
    prompt = """
You are tasked with cleaning up the following markdown text. You should return only the cleaned up markdown text. Do not explain your output or reasoning. \n remove any irrelevant text from the markdown, returning the cleaned up version of the content. Examples include any images []() or 'click here' or 'Listen to this article' or page numbers or logos.
"""
    text = """
    # TEXT TO CLEAN
    {multimodal_text}
    """
    format_text = text.format(multimodal_text=multimodal_object['text'])
    response = await asynch_client.responses.parse(
        model="gpt-4.1-mini",
        input=[{"role": "system", "content": prompt}, {"role": "user", "content": format_text}],
        text_format=MarkdownText
    )

    # convert to a json object
    response_json = json.loads(response.output_text)

    return response_json


if __name__ == "__main__":
    asyncio.run(extract_text_from_pdf(path_for_the_db="./new_publication", pdf_path=Path("C:\\Users\\dario\\OneDrive\\università\\MA\\Thesis\\microscope-toolset\\microscope-toolset\\publications\\publication_1.pdf")))

    # asyncio.run(extract_text_from_pdfs(path_for_the_db="./new_publication",
    #                                    pdfs_path="C:\\Users\\dario\\OneDrive\\università\\MA\\Thesis\\microscope-toolset\\microscope-toolset\\publications"))