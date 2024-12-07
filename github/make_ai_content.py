import requests
from urllib.parse import urlparse
import base64
from llm import call_llm
import json

def has_readme(full_name):
    url = f'https://api.github.com/repos/{full_name}/contents/'
    response = requests.get(url)
    if response.status_code == 200:
        files = response.json()
        for file in files:
            if file['name'].lower() == 'readme.md':
                return True
    return False

def get_raw_readme_content(github_url):
    # Parse the GitHub URL to extract owner and repo
    parsed_url = urlparse(github_url)
    path_parts = parsed_url.path.strip('/').split('/')
    owner, repo = path_parts[0], path_parts[1]
    # GitHub API endpoint for README
    api_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    # Make request to GitHub API
    response = requests.get(api_url)
    response.raise_for_status()  # Raise exception for bad status codes
    # Decode content (GitHub API returns base64 encoded content)
    content = base64.b64decode(response.json()['content']).decode('utf-8')
    return content

def get_prompt(readme_content):
    prompt = f"""
    You are a helpful assistant that extracts the most important parts of a readme from a github repo. You need to make a summary of the readme in bullet points.
    You need to return in JSON format. You only can use bullet points and nothing else. Make it as compact as possible. In the case the content is not english, you always need to translate it to english.

    The summary contains of three parts which you always have to include and for which you need to make the bullet points:

    1. Key features from this github repo
    2. Use cases
    3. Technical highlights

    In the case its not possible to extract something for a part, just add one bullet point saying "No information available based on the readme."

    Here is the readme:

    {readme_content}

    Here is an JSON example how you have to return the summary:

    {{
      "features": [
        "bullet point",
        "bullet point",
        "bullet point"
      ],
      "use cases": [
        "bullet point",
        "bullet point",
        "bullet point"
      ],
      "technical highlights": [
        "bullet point",
        "bullet point",
        "bullet point"
      ]
    }}

    Return in JSON:
    """
    return prompt

def get_readme_ai_analysis(github_url):
    raw_readme_content = get_raw_readme_content(github_url)
    prompt = get_prompt(raw_readme_content)
    ai_response = call_llm(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.0,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    json_response = json.loads(ai_response.choices[0].message.content)  
    return json_response

def get_ai_content(github_url, title):
    if has_readme(title) is False:
        return False
    readme_ai_analysis = get_readme_ai_analysis(github_url)
    return readme_ai_analysis