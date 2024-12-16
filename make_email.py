"""
need to iterate over all of the supabase tables and create the email from it.
"""
from supabase import create_client
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import os 

# Load environment variables from .env file
load_dotenv()

# Load environment variables for Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_latest_news():
    try:
        # Get latest posts from each table
        arxiv_latest = supabase.table('agentic_news_arxiv') \
            .select('posts') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()

        github_latest = supabase.table('agentic_news_github') \
            .select('posts') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()

        hackernews_latest = supabase.table('agentic_news_hackernews') \
            .select('posts') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()

        reddit_latest = supabase.table('agentic_news_reddit') \
            .select('posts') \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()

        # Extract posts from the response
        latest_news = {
            'arxiv': arxiv_latest.data[0]['posts'] if arxiv_latest.data else [],
            'github': github_latest.data[0]['posts'] if github_latest.data else [],
            'hackernews': hackernews_latest.data[0]['posts'] if hackernews_latest.data else [],
            'reddit': reddit_latest.data[0]['posts'] if reddit_latest.data else []
        }

        return latest_news

    except Exception as e:
        print(f"Error fetching latest news: {str(e)}")
        return None