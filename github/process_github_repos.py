import uuid  
import os
import requests
from dotenv import load_dotenv
import boto3
from llm import call_llm
from botocore.exceptions import NoCredentialsError
from .make_github_graph import get_graph_url
from .make_ai_content import get_ai_content
from playwright.sync_api import sync_playwright
import boto3
import os

# Load environment variables from .env file
load_dotenv()

def has_readme(full_name):
    url = f'https://api.github.com/repos/{full_name}/contents/'
    response = requests.get(url)
    if response.status_code == 200:
        files = response.json()
        for file in files:
            if file['name'].lower() == 'readme.md':
                return True
    return False

def get_readme_url(url):
    # Extract owner/repo from the GitHub URL
    full_name = url.split('github.com/')[1]
    api_url = f'https://api.github.com/repos/{full_name}/contents/'
    
    response = requests.get(api_url)
    if response.status_code == 200:
        files = response.json()
        for file in files:
            if file['name'].lower() == 'readme.md':
                return file['html_url']  # This returns the actual HTML view URL
    return url

def get_url_for_screenshot(full_name, url):
    if has_readme(full_name):
        readme_url = get_readme_url(url)
        return readme_url
    else:
        return url

def make_screenshot(full_name, url):
    screenshot_url = get_url_for_screenshot(full_name, url)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Set a fixed viewport size for consistent screenshots
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},  # Adjusted height for better preview
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        page = context.new_page()
        
        try:
            # Navigate to the page
            page.goto(screenshot_url, wait_until='domcontentloaded')
            
            # Try to wait for ideal conditions
            try:
                page.wait_for_selector('article, .markdown-body, #readme', timeout=30000)
                page.wait_for_timeout(2000)
            except Exception as e:
                print(f"Warning: Timeout waiting for content selectors: {e}")
                page.wait_for_timeout(5000)
            
            # Take screenshot of just the viewport (no full_page=True)
            screenshot_bytes = page.screenshot(
                type='png',
                clip={
                    'x': 0,
                    'y': 0,
                    'width': 1280,
                    'height': 800
                }
            )
            
            unique_uuid = str(uuid.uuid4().int)[:16]
            filename = f"{unique_uuid}.png"
            s3_url = upload_to_s3(screenshot_bytes, filename)
            
            return s3_url
            
        except Exception as e:
            print(f"Error during page load for {full_name}: {e}")
            # Try to take a screenshot anyway, even if there were errors
            try:
                screenshot_bytes = page.screenshot(
                    full_page=True,
                    type='png'
                )
                unique_uuid = str(uuid.uuid4().int)[:16]
                filename = f"{unique_uuid}.png"
                s3_url = upload_to_s3(screenshot_bytes, filename)
                return s3_url
            except Exception as screenshot_error:
                print(f"Failed to take error screenshot: {screenshot_error}")
                raise e
        finally:
            browser.close()

def upload_to_s3(screenshot_bytes, filename):
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
    )
    
    bucket_name = os.environ.get('S3_BUCKET_NAME')

    # Upload to S3
    s3.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=screenshot_bytes,
        ContentType='image/png'
    )
    
    # Generate S3 URL
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
    
    return s3_url

def process_github_repos_to_json(repos):
    repos_data = []
    for repo in repos:
        repo_data = {
            "title": repo['full_name'],
            "url": repo['html_url'],
            "language": repo['language'],
            "total_stars": repo['total_stars'],
            "stars_today": repo['stars_today'],
            "forks_count": repo['forks_count'],
            "screenshot": make_screenshot(repo['full_name'], repo['html_url']),
            "graph_url": get_graph_url(repo['html_url']),
            "ai_content": get_ai_content(repo['html_url'], repo['full_name'])
        }
        repos_data.append(repo_data)
    return repos_data