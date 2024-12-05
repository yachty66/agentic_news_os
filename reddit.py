"""
support for the following subreddits:

https://www.reddit.com/r/MachineLearning/
https://www.reddit.com/r/singularity/
https://www.reddit.com/r/ArtificialInteligence/
https://www.reddit.com/r/OpenAI/
https://www.reddit.com/r/StableDiffusion/
https://www.reddit.com/r/LocalLLaMA/
https://www.reddit.com/r/ClaudeAI/
https://www.reddit.com/r/perplexity_ai/


my idea is to take the top post for each sub per day and then have this post summarisedd 

"""
import praw
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from llm import call_llm
import json
from supabase import create_client, Client

# Load environment variables from .env file
load_dotenv()

# Load environment variables for Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

load_dotenv()

def get_top_post_today(subreddit_name):
    """Get the single top post from today for a given subreddit."""
    # Initialize Reddit client
    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT"),
    )
    
    # Get the top submission of today
    submission = next(reddit.subreddit(subreddit_name).top(time_filter='day', limit=1))
    
    # Return single post data
    return {
        'title': submission.title,
        'score': submission.score,
        'url': submission.url,
        'post_url': f"https://reddit.com{submission.permalink}",
        'num_comments': submission.num_comments,
        'created_utc': submission.created_utc,
        'upvote_ratio': submission.upvote_ratio,
        'author': str(submission.author),
        'content': submission.selftext if submission.is_self else None,
        'flair': submission.link_flair_text
    }

def metadata_post(post):
    title=post['title']
    score=post['score']
    url=post['post_url']
    num_comments=post['num_comments']
    content = post['content'] if post['content'] else ""  # Set default empty string if no content
    return title, score, url, num_comments, content

def summarize_reddit_posts(reddit_post):
    prompt = f"""
    You are getting as input the top reddit post from a subreddit for today.

    You need to make a short summary about what the post is about.

    Here is the reddit post:

    ---
    {reddit_post}
    ---

    You need to return your result in JSON format like this:

    {{
        "summary": "summary"
    }}

    In the case you are are getting confused by an post because it contains content you cannot handle just return an empty string. If there is no content in a post just respond with an empty string.

    Return in JSON:
    """

    response = call_llm(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        temperature=0.0,
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.choices[0].message.content)["summary"]

def add_reddit_news_to_database(ai_posts):
    data = {
        "posts": ai_posts,
    }
    try:
        response = supabase.table("agentic_news_reddit").insert(data).execute()
        print("Successfully added posts to database")
        return response
    except Exception as e:
        print(f"Error adding posts to database: {e}")
        return None

if __name__ == "__main__":
    # List of subreddits to monitor
    subreddits = [
        "MachineLearning",
        "singularity",
        "ArtificialInteligence",
        "OpenAI",
        "StableDiffusion",
        "LocalLLaMA",
        "ClaudeAI",
        "perplexity_ai"
    ]
    
    # List to store all posts
    all_posts = []
    
    # Iterate over each subreddit
    for subreddit_name in subreddits:
        try:
            top_post = get_top_post_today(subreddit_name)
            post_metadata = metadata_post(top_post)
            summary = summarize_reddit_posts(post_metadata)
            dict_post = {
                "subreddit": subreddit_name,  # Added subreddit name to identify source
                "title": post_metadata[0],
                "url": post_metadata[2],
                "score": post_metadata[1],
                "num_comments": post_metadata[3],
                "summary": summary
            }
            
            all_posts.append(dict_post)
            
        except Exception as e:
            print(f"Error processing subreddit {subreddit_name}: {str(e)}")
            continue
    
    add_reddit_news_to_database(all_posts)