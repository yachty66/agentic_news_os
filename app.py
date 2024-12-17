from get_data import run_arxiv_news, run_github_news, run_hackernews_news, run_reddit_news
from make_email import main as make_email_main

def main():
    # Gets all the new data adds it to database and sends email
    run_arxiv_news()
    run_github_news()
    run_hackernews_news()
    run_reddit_news()
    make_email_main()

if __name__ == "__main__":
    main()