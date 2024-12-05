import arxiv
from datetime import datetime, timedelta
from get_mendeley_reader_counts import add_reader_counts
from generate_arxivnews_json import process_arxiv_papers_to_json
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load environment variables for Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_date_range():
    end_date = datetime.now().date() - timedelta(days=1)
    start_date = end_date - timedelta(days=7)
    return start_date, end_date

def create_arxiv_query(start_date, end_date):
    date_range = f"{start_date.strftime('%Y%m%d')}2359 TO {end_date.strftime('%Y%m%d')}2359"
    return f"cat:cs.AI AND submittedDate:[{date_range}]"

def fetch_arxiv_query(query):
    search = arxiv.Search(
        query=query,
        max_results=None,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    return list(search.results())

def strip_version(paper_id):
    return paper_id.split('v')[0] if 'v' in paper_id else paper_id

def extract_paper_info(paper):
    return {
        'paper_id': strip_version(paper.get_short_id()),
        'category': paper.primary_category,
        'title': paper.title,
    }

def fetch_arxiv_data():
    start_date, end_date = get_date_range()
    query = create_arxiv_query(start_date, end_date)
    papers = fetch_arxiv_query(query)
    papers_info = [extract_paper_info(paper) for paper in papers]
    papers_info_with_reader_count = add_reader_counts(papers_info)
    return papers_info_with_reader_count

def is_new_paper(paper_id, user_papers):
    if user_papers is None:
        return True
    stripped_id = strip_version(paper_id)
    return not any(stripped_id == strip_version(up) for up in user_papers)

def is_in_user_categories(paper, user_categories):
    return paper['category'] in user_categories['categories']

def filter_by_newness(papers, user_data):
    user_papers = user_data.get('papers')
    return [paper for paper in papers if is_new_paper(paper['paper_id'], user_papers)]

def filter_by_categories(new_papers, user_categories):
    return [paper for paper in new_papers if is_in_user_categories(paper, user_categories)]

def get_top_papers_by_reader_count(papers, top_n=3):
    sorted_papers = sorted(papers, key=lambda x: x.get('reader_count', 0), reverse=True)
    return sorted_papers[:top_n]

def filter_arxiv_papers(user_data, papers):
    new_papers = filter_by_newness(papers, user_data)
    category_filtered_papers = filter_by_categories(new_papers, user_data['categories'])
    top_papers = get_top_papers_by_reader_count(category_filtered_papers)
    return top_papers 

def get_top_three_papers_by_reader_count(papers):
    # Sort the papers by reader count in descending order
    sorted_papers = sorted(papers, key=lambda x: x.get('reader_count', 0), reverse=True)
    # Return the top three papers
    return sorted_papers[:3]

def add_arxiv_news_to_database(ai_posts):
    data = {
        "posts": ai_posts,
    }
    try:
        response = supabase.table("agentic_news_arxiv").insert(data).execute()
        print("Successfully added posts to database")
        return response
    except Exception as e:
        print(f"Error adding posts to database: {e}")
        return None

####generate the email
if __name__ == "__main__":
    # Fetch papers
    papers = fetch_arxiv_data()

    top_three_papers = get_top_three_papers_by_reader_count(papers)

    # Process papers to get enriched JSON data
    papers_json = process_arxiv_papers_to_json(top_three_papers)

    add_arxiv_news_to_database(papers_json)