from supabase import create_client
import resend 
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import os 
from llm import call_llm
import json
import replicate
import boto3
import io
from botocore.exceptions import NoCredentialsError
import uuid

# Load environment variables from .env file
load_dotenv()

# Load environment variables for Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

resend.api_key = os.getenv("RESEND_API_KEY")

def get_latest_news():
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
    
def create_html_email(news_data):
    # Common styles
    section_style = "background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,132,199,0.1);"
    heading_style = "color: #0084C7; margin-bottom: 15px;"
    list_style = "list-style-type: none; padding-left: 0;"
    list_item_style = "margin-bottom: 15px;"
    toc_link_style = "color: #0084C7; text-decoration: none; padding: 8px 15px; background-color: white; border-radius: 4px; display: inline-block; width: 100%; box-shadow: 0 2px 4px rgba(0,132,199,0.1); transition: all 0.2s ease;"
    body_text_style = "font-size: 16px; line-height: 1.6; color: #2c3e50;"
    separator_style = "border-top: 2px dashed #e0e0e0; margin: 30px 0;"
    secondary_section_style = "background-color: #f8fafc; border-radius: 8px; padding: 15px; margin-bottom: 15px; border: 1px solid #e2e8f0;"

    def create_section_nav():
        return f"""
        <div style="text-align: right; margin-top: 20px;">
            <a href="#top" style="color: #0084C7; text-decoration: none; font-size: 14px; padding: 5px 10px; background-color: #f8fafc; border-radius: 4px;">
                ↑ Back to top
            </a>
        </div>
        """

    def create_section_summary(title, count, description):
        return f"""
        <div style="{secondary_section_style}">
            <p style="margin: 0; {body_text_style}">
                <strong>{title}:</strong> Showing {count} items. {description}
            </p>
        </div>
        """

    def create_metadata_badge(icon, text, color="#f3f8fa"):
        return f"""
        <span style="background-color: {color}; padding: 5px 10px; border-radius: 4px; margin-right: 10px; font-size: 14px;">
            {icon} {text}
        </span>
        """

    # Table of contents with improved styling
    toc_html = f"""
    <div style="{section_style}">
        <h2 style="{heading_style}">📋 Today's Agentic News</h2>
        <div style="{secondary_section_style}; margin-bottom: 20px;">
            <p style="{body_text_style}">A curated selection of today's most important AI developments.</p>
        </div>
        <ul style="{list_style}">
            <li style="{list_item_style}">
                <a href="#arxiv" style="{toc_link_style}">
                    📚 Research Papers ({len(news_data['arxiv'])} papers)
                    {create_metadata_badge('⏱️', f"{len(news_data['arxiv']) * 3}min read")}
                </a>
            </li>
            <li style="{list_item_style}">
                <a href="#github" style="{toc_link_style}">
                    💻 GitHub Trends ({len(news_data['github'])} repos)
                    {create_metadata_badge('⏱️', f"{len(news_data['github']) * 2}min read")}
                </a>
            </li>
            <li style="{list_item_style}">
                <a href="#hackernews" style="{toc_link_style}">
                    🔥 HackerNews ({len(news_data['hackernews'])} posts)
                    {create_metadata_badge('⏱️', f"{len(news_data['hackernews'])}min read")}
                </a>
            </li>
            <li style="{list_item_style}">
                <a href="#reddit" style="{toc_link_style}">
                    🎯 Reddit ({len(news_data['reddit'])} discussions)
                    {create_metadata_badge('⏱️', f"{len(news_data['reddit']) * 2}min read")}
                </a>
            </li>
        </ul>
    </div>
    """

    def create_arxiv_section(papers):
        papers_html = ""
        for i, paper in enumerate(papers, 1):
            papers_html += f"""
            <div style="{section_style}">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <span style="background-color: #0084C7; color: white; padding: 5px 10px; border-radius: 4px; margin-right: 10px;">
                        Paper {i}/{len(papers)}
                    </span>
                    {create_metadata_badge('📄', 'Research Paper')}
                    {create_metadata_badge('⏱️', '3min read')}
                </div>
                
                <h2 style="{heading_style}">{paper['title']}</h2>
                <img src="{paper['image_url']}" alt="Paper visualization" style="max-width: 100%; height: auto; border-radius: 8px; margin-bottom: 20px;" />
                
                <div style="{secondary_section_style}">
                    <h3 style="{heading_style}">Key Results</h3>
                    <ul style="{list_style}">
                        {''.join(f'<li style="{list_item_style}">• {result}</li>' for result in paper['ai_summary']['results'])}
                    </ul>
                </div>

                <div style="{secondary_section_style}">
                    <h3 style="{heading_style}">Key Insights</h3>
                    <ul style="{list_style}">
                        {''.join(f'<li style="{list_item_style}">• {insight}</li>' for insight in paper['ai_summary']['insights'])}
                    </ul>
                </div>

                <p style="text-align: center; margin-top: 20px;">
                    <a href="{paper['paper_url']}" style="background-color: #0084C7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; transition: all 0.2s ease;">
                        Read the full paper →
                    </a>
                </p>
            </div>
            """
        return papers_html

    def create_github_section(repos):
        repos_html = ""
        for i, repo in enumerate(repos, 1):
            repos_html += f"""
            <div style="{section_style}">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <span style="background-color: #0084C7; color: white; padding: 5px 10px; border-radius: 4px; margin-right: 10px;">
                        Repo {i}/{len(repos)}
                    </span>
                    {create_metadata_badge('🔤', repo['language'] if repo['language'] != 'Unknown' else 'No language')}
                    {create_metadata_badge('⭐', f"{repo['stars_today']} stars today")}
                    {create_metadata_badge('🔄', f"{repo['forks_count']} forks")}
                </div>

                <h2 style="{heading_style}">
                    <a href="{repo['url']}" style="color: #0084C7; text-decoration: none;">{repo['title']}</a>
                </h2>

                <img src="{repo['screenshot']}" alt="Repository Screenshot" style="max-width: 100%; height: auto; border-radius: 8px; margin-bottom: 20px;" />
                
                <div style="{secondary_section_style}">
                    <h3 style="{heading_style}">Key Features</h3>
                    <ul style="{list_style}">
                        {''.join(f'<li style="{list_item_style}">• {feature}</li>' for feature in repo['ai_content']['features'])}
                    </ul>
                </div>
            </div>
            """
        return repos_html

    def create_hackernews_section(posts):
        posts_html = ""
        for i, post in enumerate(posts, 1):
            posts_html += f"""
            <div style="{section_style}">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    {create_metadata_badge('📰', 'HN Discussion')}
                </div>
                <h3 style="{heading_style}">
                    <a href="{post['link']}" style="color: #0084C7; text-decoration: none;">{post['title']}</a>
                </h3>
            </div>
            """
        return posts_html

    def create_reddit_section(posts):
        posts_html = ""
        for i, post in enumerate(posts, 1):
            posts_html += f"""
            <div style="{section_style}">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    {create_metadata_badge('💬', f"r/{post['subreddit']}")}
                    {create_metadata_badge('⬆️', str(post['score']))}
                    {create_metadata_badge('💭', f"{post['num_comments']} comments")}
                </div>
                <h3 style="{heading_style}">
                    <a href="{post['url']}" style="color: #0084C7; text-decoration: none;">{post['title']}</a>
                </h3>
                <p style="{body_text_style}">{post['summary']}</p>
            </div>
            """
        return posts_html

    # Main email template with improved structure
    email_html = f"""
    <div id="top" style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f3f8fa;">
        <h1 style="{heading_style} text-align: center; border-bottom: 2px solid #0084C7; padding-bottom: 10px;">
            Agentic News
        </h1>
        
        {toc_html}
        
        <div style="{separator_style}"></div>
        
        <div id="arxiv" style="margin-bottom: 40px;">
            <h2 style="{heading_style}">📚 Latest Research Papers</h2>
            {create_section_summary("Research Papers", len(news_data['arxiv']), "Latest academic research in AI and machine learning.")}
            {create_arxiv_section(news_data['arxiv'])}
            {create_section_nav()}
        </div>

        <div style="{separator_style}"></div>

        <div id="github" style="margin-bottom: 40px;">
            <h2 style="{heading_style}">💻 Trending on GitHub</h2>
            {create_section_summary("GitHub Repositories", len(news_data['github']), "Most popular AI-related repositories today.")}
            {create_github_section(news_data['github'])}
            {create_section_nav()}
        </div>

        <div style="{separator_style}"></div>

        <div id="hackernews" style="margin-bottom: 40px;">
            <h2 style="{heading_style}">🔥 HackerNews Highlights</h2>
            {create_section_summary("HackerNews Posts", len(news_data['hackernews']), "Top AI discussions from the HN community.")}
            {create_hackernews_section(news_data['hackernews'])}
            {create_section_nav()}
        </div>

        <div style="{separator_style}"></div>

        <div id="reddit" style="margin-bottom: 40px;">
            <h2 style="{heading_style}">🎯 Reddit Discussions</h2>
            {create_section_summary("Reddit Posts", len(news_data['reddit']), "Popular AI discussions across Reddit.")}
            {create_reddit_section(news_data['reddit'])}
            {create_section_nav()}
        </div>

        <div style="{separator_style}"></div>

        <div style="background-color: #0084C7; color: white; padding: 20px; text-align: center; border-radius: 8px;">
            <p style="margin-bottom: 10px;">Found this digest helpful? Share it with your network!</p>
            <p style="margin: 0;">
                <a href="https://billing.stripe.com/p/login/8wM6sgbLWa0DaSQ8ww" target="_blank" rel="noopener noreferrer" style="color: #ffffff; text-decoration: underline;">Manage subscription</a> • 
                <a href="#top" style="color: #ffffff; text-decoration: underline;">Back to top</a>
            </p>
        </div>
    </div>
    """
    
    return email_html

def make_email_subject_and_summary(ai_news):
    prompt = f"""
    You are receiving daily AI news from different news platforms.

    You need to find a good email subject and a short one-sentence summary for the content that I can use as an email title, and the summary will be used online for the blog.

    The subject should include up to three different keywords that appear in the news, such as "o1 API, 4o/4o-mini in Realtime API + WebRTC, DPO Finetuning."

    Here are all of the AI news:

    ---
    {ai_news}
    ---

    You need to return your result containing the title and the summary in JSON format like this:

    {{
        "result": [
            {{
                "title": "title",
                "summary": "summary"
            }}
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
    ai_news_json = json.loads(response.choices[0].message.content)["result"]
    title = ai_news_json[0]["title"]
    summary = ai_news_json[0]["summary"]
    return title, summary

def add_email_to_database(title, summary, email_html, image):
    try:
        supabase.table('agentic_news_email').insert({
            "title": title,
            "summary": summary,
            "email": email_html,
            "image": image
        }).execute()
        print("Successfully inserted news into database")
    except Exception as e:
        print(f"Error inserting into database: {e}")

def get_subscribers():
    try:
        response = supabase.table('subscriptions').select('email').execute()
        return [record['email'] for record in response.data]
    except Exception as e:
        print(f"Error fetching subscribers: {e}")
        return []

def send_email_to_subscribers(html_content, title):
    # footer_message = """
    # <div style="background-color: #0084C7; color: white; padding: 20px; text-align: center; border-radius: 8px;">
    #     <p>Manage your subscription <a href="https://billing.stripe.com/p/login/8wM6sgbLWa0DaSQ8ww" target="_blank" rel="noopener noreferrer" style="color: #ffffff; text-decoration: underline;">here</a>.</p>
    #     <p>To change your categories, please reply to this email with your preferences.</p>
    # </div>
    # """
    
    wrapped_html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; background-color: #f3f8fa;">
        {html_content}
    </div>
    """

    subscribers = get_subscribers()
    if not subscribers:
        print("No subscribers found")
        return

    for subscriber_email in subscribers:
        params = {
            "from": "Agentic News <newsletter@pantheon.so>",
            "to": [subscriber_email],
            "subject": title,
            "html": wrapped_html_content,
        }

        try:
            email = resend.Emails.send(params)
            print(f"Email sent successfully to {subscriber_email}: {email}")
        except Exception as e:
            print(f"Error sending email to {subscriber_email}: {e}")


def make_image(title):
    # Check if token is available
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("Warning: REPLICATE_API_TOKEN not found")
        return None
        
    # Set token explicitly
    os.environ["REPLICATE_API_TOKEN"] = replicate_token
    
    # Generate image using Replicate
    input = {
        "prompt": title,
        "prompt_upsampling": True
    }

    try:
        output = replicate.run(
            "black-forest-labs/flux-1.1-pro",
            input=input
        )
        
        # Read the image content
        image_content = output.read()
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        object_name = f"output_{unique_id}.jpg"
        
        # Upload to S3
        s3_client = boto3.client('s3')
        try:
            s3_client.upload_fileobj(
                io.BytesIO(image_content), 
                'arxivgptnewsletter',  
                object_name
            )
            print(f"Upload Successful: {object_name}")
            return f"https://arxivgptnewsletter.s3.amazonaws.com/{object_name}"
        except NoCredentialsError:
            print("AWS Credentials not available")
            return None
        except Exception as e:
            print(f"An S3 error occurred: {e}")
            return None
    except Exception as e:
        print(f"A Replicate error occurred: {e}")
        return None
        

def main():
    news = get_latest_news()
    email_html = create_html_email(news)
    title, summary = make_email_subject_and_summary(news)
    image = make_image(title)
    print("news", news)
    print("email_html", email_html)
    print("title", title)
    print("summary", summary)
    print("image", image)
    # Call the function to add data to database
    add_email_to_database(
        title=title,
        summary=summary,
        email_html=email_html,
        image=image
    )
    send_email_to_subscribers(email_html, title)

if __name__ == "__main__":
    # main()
    image=make_image("Recent advancements in AI include the introduction of ModernBERT for efficient long-context processing, concerns over alignment faking in large language models, and a new dataset for humanoid robot pose control leveraging massive human videos.")
    print("image", image)