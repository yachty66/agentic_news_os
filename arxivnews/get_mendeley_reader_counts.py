"""
#0. get code from https://api.mendeley.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri=http://localhost/&response_type=code&scope=all

#1. need to send the request to get my access and refresh token:
curl -X POST https://api.mendeley.com/oauth/token \
  -d "grant_type=authorization_code" \
  -d "code={AUTHORIZATION_CODE}" \
  -d "redirect_uri=http://localhost/" \
  -d "client_id={CLIENT_ID}" \
  -d "client_secret={CLIENT_SECRET}"

#2. make request to get id for paper
curl 'https://api.mendeley.com/catalog?arxiv={ARXIV_ID}' \
-H 'Authorization: Bearer {ACCESS_TOKEN}' \
-H 'Accept: application/vnd.mendeley-document.1+json'

#3. make request with id to get reader count
curl 'https://api.mendeley.com/catalog/{PAPER_ID}?view=stats' \
-H 'Authorization: Bearer {ACCESS_TOKEN}' \
-H 'Accept: application/vnd.mendeley-document.1+json'

#4. get new access token with refresh token if step 2 or 3 returns an empty list
curl -X POST https://api.mendeley.com/oauth/token \
  -d "grant_type=refresh_token" \
  -d "refresh_token={REFRESH_TOKEN}" \
  -d "client_id={CLIENT_ID}" \
  -d "client_secret={CLIENT_SECRET}"

#next i need a method which returns me the reader count given an url as input
"""
import os
import json
import subprocess
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

# Get environment variables
MENDELEY_REFRESH_TOKEN = os.getenv("MENDELEY_REFRESH_TOKEN")
MENDELEY_CLIENT_ID = os.getenv("MENDELEY_CLIENT_ID")
MENDELEY_CLIENT_SECRET = os.getenv("MENDELEY_CLIENT_SECRET")

def get_access_token():
    # Check if all required variables are set
    if not all([MENDELEY_REFRESH_TOKEN, MENDELEY_CLIENT_ID, MENDELEY_CLIENT_SECRET]):
        raise ValueError("Missing required environment variables. Please check your .env file.")

    command = [
        "curl", "-X", "POST", "https://api.mendeley.com/oauth/token",
        "-d", f"grant_type=refresh_token",
        "-d", f"refresh_token={MENDELEY_REFRESH_TOKEN}",
        "-d", f"client_id={MENDELEY_CLIENT_ID}",
        "-d", f"client_secret={MENDELEY_CLIENT_SECRET}"
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    response_data = json.loads(result.stdout)
    access_token = response_data.get("access_token")
    return access_token

def get_paper_id(arxiv_id, access_token):
    command = f"curl 'https://api.mendeley.com/catalog?arxiv={arxiv_id}' " \
              f"-H 'Authorization: Bearer {access_token}' " \
              "-H 'Accept: application/vnd.mendeley-document.1+json'"

    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    # Add error handling and debugging
    if result.returncode != 0:
        print(f"Error executing curl command: {result.stderr}")
        return None

    try:
        response_data = json.loads(result.stdout)
        if not response_data:  # Check if the list is empty
            return None
        return response_data[0].get("id")
    except json.JSONDecodeError:
        print(f"Failed to parse JSON. Raw output: {result.stdout}")
        return None

def get_reader_count(access_token, paper_id):
    try:
        command = f"curl 'https://api.mendeley.com/catalog/{paper_id}?view=stats' " \
                  f"-H 'Authorization: Bearer {access_token}' " \
                  "-H 'Accept: application/vnd.mendeley-document.1+json'"

        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error executing curl command: {result.stderr}")
            return 0

        response_data = json.loads(result.stdout)
        
        reader_count = response_data.get("reader_count")
        if reader_count is None:
            print(f"No reader count available for paper_id: {paper_id}")
            return 0
        
        return reader_count

    except Exception as e:
        print(f"An error occurred while getting reader count for paper_id {paper_id}: {str(e)}")
        return 0

def get_mendeley_paper_id(arxiv_id, access_token):
    return get_paper_id(arxiv_id, access_token)

def get_paper_reader_count(mendeley_paper_id, access_token):
    return get_reader_count(access_token, mendeley_paper_id) if mendeley_paper_id else 0

def add_reader_count_to_paper(paper, access_token):
    mendeley_paper_id = get_mendeley_paper_id(paper['paper_id'], access_token)
    reader_count = get_paper_reader_count(mendeley_paper_id, access_token)
    return {**paper, 'reader_count': reader_count}

def add_reader_counts(papers, max_workers=100):
    access_token = get_access_token()
    arxiv_ids = [paper['paper_id'] for paper in papers]
    paper_ids = get_paper_ids_parallel(arxiv_ids, access_token, max_workers)
    
    def process_paper(paper):
        mendeley_paper_id = paper_ids.get(paper['paper_id'])
        reader_count = get_paper_reader_count(mendeley_paper_id, access_token) if mendeley_paper_id else 0
        return {**paper, 'reader_count': reader_count}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(process_paper, papers))

def get_paper_ids_parallel(arxiv_ids, access_token, max_workers=100):
    paper_ids = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_arxiv = {executor.submit(get_paper_id, arxiv_id, access_token): arxiv_id for arxiv_id in arxiv_ids}
        for future in as_completed(future_to_arxiv):
            arxiv_id = future_to_arxiv[future]
            try:
                paper_id = future.result()
                if paper_id:
                    paper_ids[arxiv_id] = paper_id
            except Exception as exc:
                print(f'{arxiv_id} generated an exception: {exc}')
    return paper_ids

# if __name__ == "__main__":
#     access_token = get_access_token()
#     print("Access Token:", access_token)

#     # Example usage with multiple papers
#     sample_papers = [
#         {'paper_id': '2409.09032'},
#         {'paper_id': '2409.09033'},
#         # ... add more sample papers as needed
#     ]
#     results = add_reader_counts(sample_papers)
#     for result in results:
#         print(f"Paper ID: {result['paper_id']}, Reader Count: {result['reader_count']}")
