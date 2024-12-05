import uuid  
import arxiv
import os
import json
import requests
import io
import fitz  
import tiktoken
from dotenv import load_dotenv
import resend
import boto3
from botocore.exceptions import NoCredentialsError
from llm import call_llm
import fitz
import io
from PIL import Image

# Load environment variables from .env file
load_dotenv()

def get_paper_info(paper_id):
    # Query the arXiv API for the paper
    search = arxiv.Search(
        query=f"id:{paper_id}",
        max_results=1,
        sort_by=arxiv.SortCriterion.Relevance
    )
    # Retrieve the first result
    for result in search.results():
        return result.title, result.summary  # Return title and abstract of the paper
    return None, None  # Return None if no paper is found

def extract_important_parts(abstract):
    prompt = f"""
    You are a helpful assistant that extracts the most important parts of an abstract from a paper. I want to highlight the text you are extracting later inside the PDF. 
    You need to return the most important parts as JSON objects; it's important that you don't change any characters from the original text and that you extract all important information.

    Here is the abstract:

    {abstract}

    {{
      "text": [
        "text to highlight",
        "text to highlight",
        "text to highlight"
      ]
    }}

    Return in JSON:
    """
    response = call_llm(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}]
    )
    print(f"response: {response.choices[0].message.content}")
    return json.loads(response.choices[0].message.content)["text"]

def download_pdf_content(arxiv_id):
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Failed to download PDF: {e}")
        return None
    
def extract_first_page(pdf_content):
    try:
        with fitz.open(stream=pdf_content, filetype="pdf") as doc:
            first_page_doc = fitz.open()
            first_page_doc.insert_pdf(doc, from_page=0, to_page=0)
            
            output_buffer = io.BytesIO()
            first_page_doc.save(output_buffer)
            first_page_doc.close()
            
            return output_buffer.getvalue()
    except Exception as e:
        print(f"Failed to process PDF: {e}")
        return None

def get_first_page_pdf(arxiv_id):
    pdf_content = download_pdf_content(arxiv_id)
    if pdf_content is None:
        return None
    return extract_first_page(pdf_content)

def highlight_abstract_parts_in_pdf_as_image(
    pdf_content,
    title_text,
    important_parts,
    dpi=300
):
    try:
        # Open the PDF from the content
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        page = doc[0]  # Access the first page of the document
        
        # Highlight the title text
        title_instances = page.search_for(title_text)
        if not title_instances:
            print(f"Title text '{title_text}' not found on the page.")
        for inst in title_instances:
            highlight = page.add_highlight_annot(inst)
            highlight.update()
        
        # Highlight the important parts from the abstract
        for part in important_parts:
            part_instances = page.search_for(part)
            if not part_instances:
                print(f"Important part '{part}' not found on the page.")
            for inst in part_instances:
                highlight = page.add_highlight_annot(inst)
                highlight.update()
        
        # Render the page to an image with higher DPI
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
        # Convert the pixmap to a PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        # Save the image to a bytes buffer
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        doc.close()
        return img_byte_arr, 'PNG'
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None, None

def upload_image_to_s3(image_content, bucket, object_name):
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_fileobj(io.BytesIO(image_content), bucket, object_name)
        print(f"Upload Successful: {object_name} to {bucket}")
        return f"https://{bucket}.s3.amazonaws.com/{object_name}"
    except NoCredentialsError:
        print("Credentials not available")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

def download_and_extract_paper_info(arxiv_id, token_limit=120000, model="gpt-3.5-turbo"):
    try:
        # Fetch paper metadata
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        # Download PDF
        response = requests.get(paper.pdf_url)
        response.raise_for_status()
        # Process PDF content
        doc = fitz.open(stream=response.content, filetype="pdf")
        encoding = tiktoken.encoding_for_model(model)
        text = ""
        tokens = []
        for page in doc:
            page_text = page.get_text()
            new_tokens = encoding.encode(page_text, disallowed_special=())
            if len(tokens) + len(new_tokens) > token_limit:
                remaining = token_limit - len(tokens)
                tokens.extend(new_tokens[:remaining])
                break
            tokens.extend(new_tokens)
            text += page_text
        return encoding.decode(tokens)
    except requests.RequestException as e:
        print(f"Failed to download PDF: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return None

def summarize_paper(paper_text):
    summary_prompt = f"""
    You are a helpful assistant that extracts the most important parts of a paper. You need to make a summary of the paper in bullet points.
    You need to return in JSON format. You only can use bullet points and nothing else. Make it as compact as possible.

    The summary contains of four parts which you always have to include and for which you need to make the bullet points:

    1. Key Insights from this Paper
    2. Original Problem
    3. Solution in this Paper
    4. Results

    Here is the paper:

    {paper_text}

    Here is an JSON example how you have to return the summary:

    {{
      "insights": [
        "bullet point",
        "bullet point",
        "bullet point"
      ],
      "problem": [
        "bullet point",
        "bullet point",
        "bullet point"
      ],
      "solution": [
        "bullet point",
        "bullet point",
        "bullet point"
      ],
      "results": [
        "bullet point",
        "bullet point",
        "bullet point"
    }}

    Return in JSON:
    """
    summary_response = call_llm(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.0,
        messages=[
            {"role": "user", "content": summary_prompt}
        ]
    )
    return json.loads(summary_response.choices[0].message.content)

def make_url(paper_id):
    return f"https://arxiv.org/abs/{paper_id}"

def process_arxiv_papers_to_json(paper_info_list):
    papers_data = []  # List to hold all paper data
    
    for paper_info in paper_info_list:
        paper_id = paper_info['paper_id']
        url = make_url(paper_id)
        title, abstract = get_paper_info(paper_id)
        
        if abstract:
            important_parts = extract_important_parts(abstract)
            pdf_content = get_first_page_pdf(paper_id)
            
            # Generate unique ID for image
            unique_id = str(uuid.uuid4())
            output_image_path = f"output_{unique_id}.png"
            
            # Generate and upload image
            image_content, _ = highlight_abstract_parts_in_pdf_as_image(pdf_content, title, important_parts)
            upload_image_to_s3(image_content, 'arxivgptnewsletter', output_image_path)
            image_url = f"https://arxivgptnewsletter.s3.amazonaws.com/{output_image_path}"
            
            # Get paper summary
            paper_text = download_and_extract_paper_info(paper_id)
            bullet_points = summarize_paper(paper_text)
            
            # Create paper data structure
            paper_data = {
                "title": title,
                "paper_url": url,
                "image_url": image_url,
                "ai_summary": bullet_points
            }
            
            papers_data.append(paper_data)
        else:
            print(f"Paper {paper_id} not found.")
    
    return papers_data

# Example usage:
# if __name__ == "__main__":
#     import json
    
#     # Process papers and get JSON data
#     papers_json = process_arxiv_papers_to_json(paper_info_list)
    
#     # Save to file (optional)
#     with open('papers_data.json', 'w', encoding='utf-8') as f:
#         json.dump(papers_json, f, ensure_ascii=False, indent=2)