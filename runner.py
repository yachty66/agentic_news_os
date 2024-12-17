from arxiv.arxivnews import main
from github.github import main
from hackernews.hackernews import main
from reddit.reddit import main

def run_arxiv_news():
    main()

def run_github_news():
    main()

def run_hackernews_news():
    main()

def run_reddit_news():
    main()

if __name__ == "__main__":
    #this should add all the new data to database
    run_arxiv_news()
    run_github_news()
    run_hackernews_news()
    run_reddit_news()