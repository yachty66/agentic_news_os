Based on the code provided, the final HTML for emails is constructed in multiple places depending on the source (GitHub, arXiv, or bioRxiv). Let me point out where the final HTML assembly happens for each:

1. For GitHub repositories:

```234:320:backend/github/email_github.py
def get_total_html(title, url, language, stargazers_count, forks_count, screenshot, graph_url, ai_content):
    # Define common styles to match arXiv newsletter
    section_style = "background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,132,199,0.1);"
    heading_style = "color: #0084C7;"
    list_style = "list-style-type: disc; padding-left: 20px;"
    list_item_style = "margin-bottom: 10px;"
    
    # Helper function to create a section
    def create_section(section_title, items):
        if not items:
            return ""
        items_html = ''.join(f'<li style="{list_item_style}">{item}</li>' for item in items)
        return f"""
        <div style="{section_style}">
            <h2 style="{heading_style}">{section_title}</h2>
            <ul style="{list_style}">
                {items_html}
            </ul>
        </div>
        """

    # Create repository stats section
    stats_html = f"""
    <div style="{section_style}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="background-color: #f3f8fa; padding: 5px 10px; border-radius: 4px; margin-right: 10px;">
                    {'🔤 ' + language if language else '📄 No language detected'}
                </span>
                <span style="background-color: #f3f8fa; padding: 5px 10px; border-radius: 4px; margin-right: 10px;">
                    ⭐ {stargazers_count} stars today
                </span>
                <span style="background-color: #f3f8fa; padding: 5px 10px; border-radius: 4px;">
                    🔄 {forks_count} forks total
                </span>
            </div>
        </div>
    </div>
    """
    # Create AI analysis sections if available
    ai_sections = ""
    if ai_content and isinstance(ai_content, dict):
        if 'features' in ai_content:
            ai_sections += create_section("Key Features", ai_content['features'])
        if 'use cases' in ai_content:
            ai_sections += create_section("Use Cases", ai_content['use cases'])
        if 'technical highlights' in ai_content:
            ai_sections += create_section("Technical Highlights", ai_content['technical highlights'])

    # Update the repository structure section with more top margin
    structure_html = f"""
    <div style="{section_style}">
        <h2 style="{heading_style}">Repository Structure</h2>
        <p style="text-align: center; margin-top: 30px;">
            <a href="{graph_url}" 
               style="background-color: #0084C7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                View Repository Structure
            </a>
        </p>
    </div>
    """

    # Construct the HTML content
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f3f8fa;">
        <h1 style="{heading_style} border-bottom: 2px solid #0084C7; padding-bottom: 10px;">
            <a href="{url}" style="color: #0084C7; text-decoration: none;">{title}</a>
        </h1>
        
        {stats_html}
        
        {ai_sections}

        {structure_html}

        <div style="{section_style}">
            <h2 style="{heading_style}">Repository Preview</h2>
            <img src="{screenshot}" alt="Repository Screenshot" style="max-width: 100%; height: auto; border-radius: 8px; margin-bottom: 20px;" />
        </div>

        <p style="text-align: center; margin-top: 30px;">
            <a href="{url}" style="background-color: #0084C7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Read the full repository</a>
        </p>
    </div>
    """
    return html_content
```

The `get_total_html()` function constructs the final HTML for each repository, including stats, AI analysis sections, repository structure, and preview.

2. For arXiv papers:

```230:264:backend/arxiv/email_arxiv.py
def construct_html_content(title, bullet_points, image_url, url):
    # Define common styles
    section_style = "background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,132,199,0.1);"
    heading_style = "color: #0084C7;"
    list_style = "list-style-type: disc; padding-left: 20px;"
    list_item_style = "margin-bottom: 10px;"

    # Helper function to create a section
    def create_section(section_title, items):
        items_html = ''.join(f'<li style="{list_item_style}">{item}</li>' for item in items)
        return f"""
        <div style="{section_style}">
            <h2 style="{heading_style}">{section_title}</h2>
            <ul style="{list_style}">
                {items_html}
            </ul>
        </div>
        """

    # Construct the HTML content
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f3f8fa;">
        <h1 style="{heading_style} border-bottom: 2px solid #0084C7; padding-bottom: 10px;">{title}</h1>

        {create_section("Key Insights", bullet_points["insights"])}
        {create_section("Original Problem", bullet_points["problem"])}
        {create_section("Solution", bullet_points["solution"])}
        {create_section("Results", bullet_points["results"])}

        <img src="{image_url}" alt="Highlighted PDF" style="max-width: 100%; height: auto; border-radius: 8px; margin-bottom: 20px;" />
        <p style="text-align: center;">
            <a href="{url}" style="background-color: #0084C7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Read the full paper</a>
        </p>
    </div>
    """
```

The `construct_html_content()` function builds the HTML for each arXiv paper.

3. For bioRxiv papers:

```202:236:backend/biorxiv/email_biorxiv.py
def construct_html_content(title, bullet_points, image_url, url):
    # Define common styles
    section_style = "background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,132,199,0.1);"
    heading_style = "color: #0084C7;"
    list_style = "list-style-type: disc; padding-left: 20px;"
    list_item_style = "margin-bottom: 10px;"

    # Helper function to create a section
    def create_section(section_title, items):
        items_html = ''.join(f'<li style="{list_item_style}">{item}</li>' for item in items)
        return f"""
        <div style="{section_style}">
            <h2 style="{heading_style}">{section_title}</h2>
            <ul style="{list_style}">
                {items_html}
            </ul>
        </div>
        """

    # Construct the HTML content
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f3f8fa;">
        <h1 style="{heading_style} border-bottom: 2px solid #0084C7; padding-bottom: 10px;">{title}</h1>

        {create_section("Key Insights", bullet_points["insights"])}
        {create_section("Original Problem", bullet_points["problem"])}
        {create_section("Solution", bullet_points["solution"])}
        {create_section("Results", bullet_points["results"])}

        <img src="{image_url}" alt="Highlighted PDF" style="max-width: 100%; height: auto; border-radius: 8px; margin-bottom: 20px;" />
        <p style="text-align: center;">
            <a href="{url}" style="background-color: #0084C7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">Read the full paper</a>
        </p>
    </div>
    """
```

The `construct_html_content()` function creates the HTML for each bioRxiv paper.

All these HTML contents are then wrapped with a common footer message when sent via email. This wrapping happens in the respective `send_email()` functions, for example in GitHub's case:

```76:89:backend/github/email_github.py
def send_email(html_content, repo_titles, user_email):
    footer_message = """
    <div style="background-color: #0084C7; color: white; padding: 20px; text-align: center; border-radius: 8px;">
        <p>Manage your subscription <a href="https://billing.stripe.com/p/login/8wM6sgbLWa0DaSQ8ww" target="_blank" rel="noopener noreferrer" style="color: #ffffff; text-decoration: underline;">here</a>.</p>
        <p>To change your categories, please reply to this email with your preferences.</p>
    </div>
    """
    
    wrapped_html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; background-color: #f3f8fa;">
        {html_content}
        {footer_message}
    </div>
    """
```