import requests
from bs4 import BeautifulSoup
from llm import call_llm
from supabase import create_client, Client
from dotenv import load_dotenv
import os 
import json

# Load environment variables from .env file
load_dotenv()

# Load environment variables for Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def extract_ai_news(hackernews_posts):
    prompt = f"""
    You are getting as input the title and link from all of the posts on the Hacker News front page.

    We are curating data for an AI newsletter, and you need to return all the titles and links of the posts that are AI-related. 

    Here is the hackernews posts:

    ---
    {hackernews_posts}
    ---

    You need to return your result in JSON format like this:

    {{
        "result": [
            {{
                "title": "title",
                "link": "link"
            }},
            {{
                "title": "title",
                "link": "link"
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

def get_hackernews_frontpage():
    # HN front page URL
    url = "https://news.ycombinator.com"
    
    # Fetch the page
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all story titles (they have class 'titleline')
        stories = []
        for story in soup.find_all('span', class_='titleline'):
            title = story.find('a').text
            link = story.find('a')['href']
            stories.append({
                'title': title,
                'link': link
            })

        return stories
    else:
        print(f"Failed to fetch HN: {response.status_code}")
        return []
    
def add_ai_news_to_database(ai_posts):
    data = {
        "posts": ai_posts,
    }
    try:
        response = supabase.table("agentic_news_hackernews").insert(data).execute()
        print("Successfully added posts to database")
        return response
    except Exception as e:
        print(f"Error adding posts to database: {e}")
        return None

if __name__ == "__main__":
    stories = get_hackernews_frontpage()
    ai_posts = extract_ai_news(stories)
    add_ai_news_to_database(ai_posts)
    print("ai_posts:", ai_posts)
