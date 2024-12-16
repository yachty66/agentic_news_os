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
        <h2 style="{heading_style}">📋 Today's AI Digest</h2>
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
            AI News Digest
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

# Generate the email HTML
email_html = create_html_email(news)

# You can then send this using Resend
# resend.emails.send({
#     "from": "onboarding@resend.dev",
#     "to": "your@email.com",
#     "subject": "AI News Digest",
#     "html": email_html
# })