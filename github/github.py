import requests
from bs4 import BeautifulSoup
from llm import call_llm
from supabase import create_client, Client
from dotenv import load_dotenv
import os 
import json
from process_github_repos import process_github_repos_to_json

# Load environment variables from .env file
load_dotenv()

# Load environment variables for Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_github_repos():
    """
    Fetch all trending GitHub repositories using web scraping
    Returns a list of repository dictionaries
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    all_repos = []
    url = "https://github.com/trending"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        repo_elements = soup.select('article.Box-row')
        
        for repo in repo_elements:
            # Extract repository information
            repo_link = repo.select_one('h2 a')
            full_name = repo_link.text.strip().replace('\n', '').replace(' ', '')
            html_url = f"https://github.com/{full_name}"
            
            description = repo.select_one('p')
            description = description.text.strip() if description else ""
            
            # Extract language (new!)
            language_element = repo.select_one('span[itemprop="programmingLanguage"]')
            language = language_element.text.strip() if language_element else "Unknown"
            
            # Get total stars and forks
            stats = repo.select('a.Link--muted')
            stars_total = stats[0].text.strip() if stats else "0"
            forks = stats[1].text.strip() if len(stats) > 1 else "0"
            
            # Get stars gained today
            stars_today_element = repo.select_one('span.d-inline-block.float-sm-right')
            stars_today = "0"
            if stars_today_element:
                stars_text = stars_today_element.text.strip()
                stars_today = stars_text.split(' ')[0]
            
            def convert_to_number(value):
                value = value.lower().strip()
                if 'k' in value:
                    return int(float(value.replace('k', '')) * 1000)
                return int(value.replace(',', ''))
            
            repo_dict = {
                'full_name': full_name,
                'html_url': html_url,
                'description': description,
                'language': language,  # Added language field
                'total_stars': convert_to_number(stars_total),
                'stars_today': convert_to_number(stars_today),
                'forks_count': convert_to_number(forks),
            }
            
            all_repos.append(repo_dict)
            
        print(f"Successfully fetched {len(repo_elements)} repositories")
            
    except Exception as e:
        print(f"Error fetching repositories: {e}")
    
    return all_repos

def get_all_unique_user_repos(user_data):
    """Get unique repository URLs from user data, handling None case"""
    if not user_data or 'repos' not in user_data or user_data['repos'] is None:
        return set()
    return set(user_data['repos'])

def filter_by_newness(repos, user_data):
    """Filter repositories by newness, handling empty user data"""
    user_repos = get_all_unique_user_repos(user_data)
    if not user_repos:
        return repos
    return [paper for paper in repos if paper['html_url'] not in user_repos]

def get_top_repos_by_stargazers_count(repos, top_n=3):
    sorted_repos = sorted(repos, key=lambda x: (int(x.get('stargazers_count') or 0)), reverse=True)
    return sorted_repos[:top_n]

def extract_ai_repos(github_repos):
    prompt = f"""
    You are getting as input all of the daily trending github repositories. each repository comes in a JSON containing full_name, html_url, description, language, total_stars, stars_today and forks_count.

    We are curating data for an AI newsletter in which we want to add information about all of those repositories. Because of that, your goal is it to find and return all the GitHub repositories that have something to do with AI.

    Here is the github repos:

    ---
    {github_repos}
    ---

    You need to return your result containing all the repositories that are AI-related in JSON format like this:

    {{
        "result": [
            {{
                "full_name": "full_name",
                "html_url": "html_url", 
                "description": "description",
                "language": "language",
                "total_stars": "total_stars",
                "stars_today": "stars_today",
                "forks_count": "forks_count"
            }},
            {{
                "full_name": "full_name",
                "html_url": "html_url", 
                "description": "description",
                "language": "language",
                "total_stars": "total_stars",
                "stars_today": "stars_today",
                "forks_count": "forks_count"
            }}
        ]
    }}

    In case you think there are no AI-related posts, you need to return an empty array.

    Return in JSON:
    """

    response = call_llm(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.choices[0].message.content)["result"]


def add_github_repos_to_database(repos_data):
    data = {
        "posts": repos_data,
    }
    supabase.table("agentic_news_github").insert(data).execute()

def main():
    repos = fetch_github_repos()
    
    # Create a formatted string of repos with clear separation
    formatted_repos = "\n---\n".join([
        f"""Repository: {repo['full_name']}
URL: {repo['html_url']}
Description: {repo['description']}
Language: {repo['language']}
Total Stars: {repo['total_stars']}
Stars Today: {repo['stars_today']}
Forks: {repo['forks_count']}"""
        for repo in repos
    ])
    
    ai_repos = extract_ai_repos(formatted_repos)
    repos_data = process_github_repos_to_json(ai_repos)
    
    print("Repos data:", repos_data)

    add_github_repos_to_database(repos_data)

    print("Done!")



if __name__ == "__main__":
    main()