import json

import pymupdf
import os
import base64
from openai import OpenAI
from pydantic import BaseModel

class ImageToMarkdown(BaseModel):
    title: str
    page_number: int
    author: str
    text: str


def load_file(file_path: str):
    """
    Load a PDF file and convert it to a png file.
    """
    # load the pdf file
    doc = pymupdf.open(filename=file_path)

    # create dir with images
    if not os.path.exists("pages_png"):
        os.makedirs("pages_png")

    # convert pdf to an image
    for page in doc:
        pix = page.get_pixmap()
        pix.save("page-%i.png" % page.number)

    # close pdf file
    doc.close()

    return "The PDFs was converted to a png."

def encode_image_to_base64(image_path):
    """
    Encode an image to base64
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")



def image_to_markdown(base64_image):
    """
    Convert an image to a Markdown text. Add metadata of the document like 'title', 'page', 'author', ect
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = "TO add"
    response = client.responses.parse(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text",
                     "text": "Extract the text from this pdf page. Add the metadata of the document."},
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