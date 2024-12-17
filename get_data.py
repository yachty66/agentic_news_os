from arxivnews.arxivnews import main as arxivnews_main
from github.github import main as github_main
from hackernews.hackernews import main as hackernews_main
from reddit.reddit import main as reddit_main

def run_arxiv_news():
    arxivnews_main()

def run_github_news():
    github_main()

def run_hackernews_news():
    hackernews_main()

def run_reddit_news():
    reddit_main()