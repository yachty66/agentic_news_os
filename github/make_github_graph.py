import os
import boto3
from treelib import Tree
import json
import tempfile
import shutil
import uuid
from git import Repo
from urllib.parse import urlparse

def clone_repo(github_url):
    """Clone the repository and return the path"""
    temp_dir = tempfile.mkdtemp()
    try:
        Repo.clone_from(github_url, temp_dir)
        return temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise e

def create_directory_tree(startpath, tree=None, parent=None, max_depth=4, max_files=10, current_depth=0):
    """Create tree with depth limit and file count limit"""
    if tree is None:
        tree = Tree()
        tree.create_node("📦", "root")
        parent = "root"
    entries = sorted(os.listdir(startpath))
    files = [e for e in entries if os.path.isfile(os.path.join(startpath, e)) and not e.startswith('.')]
    dirs = [e for e in entries if os.path.isdir(os.path.join(startpath, e)) and not e.startswith('.')]
    # Handle files
    if len(files) > max_files:
        tree.create_node(f"📄 {len(files)} files", f"{parent}_files", parent=parent)
    else:
        for entry in files:
            path = os.path.join(startpath, entry)
            node_id = path.replace('\\', '/').replace(' ', '_')
            tree.create_node(f"📄 {entry}", node_id, parent=parent)
    # Handle directories
    for entry in dirs:
        path = os.path.join(startpath, entry)
        node_id = path.replace('\\', '/').replace(' ', '_')
        tree.create_node(f"📁 {entry}", node_id, parent=parent)
        create_directory_tree(path, tree, node_id, max_depth, max_files, current_depth + 1)
    return tree

def tree_to_dict(tree):
    def _to_dict(node_id):
        node = tree.get_node(node_id)
        children = tree.children(node_id)
        
        if not children:
            return {"name": node.tag, "id": node.identifier}
        
        return {
            "name": node.tag,
            "id": node.identifier,
            "children": [_to_dict(child.identifier) for child in children]
        }
    
    return _to_dict("root")
    
def generate_html(tree_dict, repo_name):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Directory Structure - {repo_name}</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                overflow: auto;  /* Allow scrolling */
                height: 100vh;  /* Full viewport height */
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .node circle {{
                fill: #fff;
                stroke: #4CAF50;
                stroke-width: 2px;
            }}
            .node text {{
                font: 14px sans-serif;
            }}
            .link {{
                fill: none;
                stroke: #ccc;
                stroke-width: 2px;
            }}
            #tree {{
                background: #f5f5f5;
                border-radius: 8px;
                padding: 20px;
                overflow: auto;  /* Allow scrolling within the tree */
            }}
        </style>
    </head>
    <body>
        <div id="tree"></div>
        <script>
            const treeData = {tree_data};

            function countFilesAndFolders(node) {{
                let count = 1; // Count the current node
                if (node.children) {{
                    node.children.forEach((child) => {{
                        count += countFilesAndFolders(child); // Recursively count children
                    }});
                }}
                return count;
            }}
            const totalCount = countFilesAndFolders(treeData);

            const width = Math.max(window.innerWidth - 100, 1200);
            const height = Math.max(totalCount * 20); // Dynamic height based on number of nodes
            const margin = {{top: 20, right: 120, bottom: 20, left: 120}};
            
            const tree = d3.tree()
                .size([height - margin.top - margin.bottom, width - margin.left - margin.right]);
            
            const svg = d3.select("#tree")
                .append("svg")
                .attr("width", width)
                .attr("height", height)
                .append("g")
                .attr("transform", `translate(${{
                    margin.left
                }},${{
                    margin.top
                }})`);
            
            const root = d3.hierarchy(treeData);
            const nodes = tree(root);
            
            const link = svg.selectAll(".link")
                .data(nodes.links())
                .enter()
                .append("path")
                .attr("class", "link")
                .attr("d", d3.linkHorizontal()
                    .x(d => d.y)
                    .y(d => d.x));  // Adjusted for more vertical space
            
            const node = svg.selectAll(".node")
                .data(nodes.descendants())
                .enter()
                .append("g")
                .attr("class", "node")
                .attr("transform", d => `translate(${{
                    d.y
                }},${{
                    d.x
                }})`);  // Adjusted for more vertical space
            
            node.append("circle")
                .attr("r", 5);
            
            node.append("text")
                .attr("dy", ".35em")
                .attr("x", d => d.children ? -13 : 13)
                .attr("text-anchor", d => d.children ? "end" : "start")
                .text(d => d.data.name);
        </script>
    </body>
    </html>
    """.format(
        repo_name=repo_name,
        tree_data=json.dumps(tree_dict)
    )
    return html

def create_visualization(github_url, output_file=None):
    """Create visualization from GitHub URL"""
    # Extract repository name from URL
    repo_name = urlparse(github_url).path.split('/')[-1]
    
    if output_file is None:
        output_file = f"{repo_name}_structure.html"
    
    # Clone repository to temporary directory
    temp_dir = None
    try:
        temp_dir = clone_repo(github_url)
        
        # Create tree structure
        tree = create_directory_tree(temp_dir)
        
        # Convert to dictionary format for D3.js
        tree_dict = tree_to_dict(tree)
        
        # Generate HTML
        html_content = generate_html(tree_dict, repo_name)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        tree.show()
        
    finally:
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    return output_file

def upload_file_to_s3_html(file_path, bucket_name, object_name=None):
    """
    Upload a file to an S3 bucket and return its URL
    """
    if object_name is None:
        object_name = os.path.basename(file_path)

    session = boto3.Session()
    s3_client = session.client('s3')

    try:
        extra_args = {
            'ContentType': 'text/html',
            'ContentDisposition': 'inline',
            'CacheControl': 'no-cache'
        }

        s3_client.upload_file(
            file_path, 
            bucket_name, 
            object_name,
            ExtraArgs=extra_args
        )
        return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        return None

def get_graph_url(github_url):
    # Create a temporary directory to store the HTML file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate random filename
        random_filename = f"github_structure_{uuid.uuid4().hex[:16]}.html"
        
        # Create full path for the temporary file
        temp_file_path = os.path.join(temp_dir, random_filename)
        
        # Create visualization with temporary file path
        file_path = create_visualization(github_url, output_file=temp_file_path)
        
        # Upload to S3 using the random filename
        bucket_name = "arxivgptnewsletter"
        
        # Upload and get URL
        s3_url = upload_file_to_s3_html(file_path, bucket_name, random_filename)
        
        if s3_url:
            return s3_url
        else:
            raise Exception("Failed to upload visualization to S3")

# Usage example
if __name__ == "__main__":
    get_graph_url("https://github.com/yachty66/experiments")