import urllib.request
import urllib.error
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import os
import datetime
import hashlib

# Define the starting URL and the number of pages to be indexed
base_url = "http://www.cse.ust.hk"
max_pages = 30

# Define the directory where the indexed pages will be stored
base_dir = "indexed_pages"
if not os.path.exists(base_dir):
    os.mkdir(base_dir)

# Define the inverted index
inverted_index = {}

# Define a function to retrieve the HTML content of a given URL
def get_html(url):
    try:
        response = urllib.request.urlopen(url)
        html = response.read()
        return html
    except:
        return None

# Define a function to parse the HTML content of a given URL
def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract the page title
    page_title = soup.title.string.strip() if soup.title else ''
    
    # Extract the last modification date, size of page
    last_modified = datetime.datetime.now()
    page_size = len(html)
    
    # Extract the keywords and their frequencies
    keywords = {}
    for word in soup.get_text().split():
        word = word.strip().lower()
        if word not in keywords:
            keywords[word] = 1
        else:
            keywords[word] += 1
            
    return page_title, last_modified, page_size, keywords

# Define a function to add a page to the index
def add_page_to_index(url, page_title, last_modified, page_size, keywords):
    if url not in inverted_index:
        inverted_index[url] = {
            "title": page_title,
            "last_modified": last_modified,
            "page_size": page_size,
            "keywords": keywords,
            "links": []
        }
    else:
        if last_modified > inverted_index[url]["last_modified"]:
            inverted_index[url] = {
                "title": page_title,
                "last_modified": last_modified,
                "page_size": page_size,
                "keywords": keywords,
                "links": inverted_index[url]["links"]
            }

# Define a function to retrieve all the hyperlinks on a given webpage
def get_links(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and not href.startswith('#'):
            full_url = urljoin(url, href)
            links.append(full_url)
    return links

# Define a function to create a file structure containing the parent/child link relation
def create_file_structure():
    file_structure = {}
    for url in inverted_index:
        page_id = hashlib.sha1(url.encode('utf-8')).hexdigest()
        file_structure[page_id] = []
        for link in inverted_index[url]["links"]:
            link_id = hashlib.sha1(link.encode('utf-8')).hexdigest()
            file_structure[page_id].append(link_id)
            if link_id not in file_structure:
                file_structure[link_id] = []
            file_structure[link_id].append(page_id)
    return file_structure

# Define a function to implement a breadth-first search strategy to recursively fetch the required number of pages from the given site
def crawl(start_url, max_pages):
    # Initialize the list of pages to be crawled
    pages_to_crawl = [start_url]
    # Initialize the list of crawled pages
    crawled_pages = []
    # Initialize the count of crawled pages
    count = 0
    
    # Implement the breadth-first search strategy
    while pages_to_crawl and count < max_pages:
        url = pages_to_crawl.pop(0)
        if url not in crawled_pages:
            html = get_html(url)
            if html:
                page_title, last_modified, page_size, keywords = parse_html(html)
                add_page_to_index(url, page_title, last_modified, page_size, keywords)
                links = get_links(html, url)
                inverted_index[url]["links"] = links
                pages_to_crawl.extend(links)
                crawled_pages.append(url)
                count += 1
                
    # Create the file structure containing the parent/child link relation
    file_structure = create_file_structure()
    
    return inverted_index, file_structure

# Define a function to handle cyclic links gracefully
def handle_cyclic_links(file_structure):
    for page_id in file_structure:
        visited = []
        stack = [page_id]
        while stack:
            current_page_id = stack.pop()
            if current_page_id not in visited:
                visited.append(current_page_id)
                stack.extend(file_structure[current_page_id])
            else:
                file_structure[current_page_id] = []
    return file_structure

# Call the spider to index 30 pages from http://www.cse.ust.hk
inverted_index, file_structure = crawl(base_url, max_pages)

# Handle cyclic links gracefully
file_structure = handle_cyclic_links(file_structure)

# Print the indexed pages and their attributes
for url in inverted_index:
    page_id = hashlib.sha1(url.encode('utf-8')).hexdigest()
    print(inverted_index[url]["title"])
    print(str(inverted_index[url]["last_modified"]) + ", " + str(inverted_index[url]["page_size"]))
    keywords = ""
    for keyword in inverted_index[url]["keywords"]:
        keywords += keyword + " " + str(inverted_index[url]["keywords"][keyword]) + "; "
    print(keywords)
    child_links = ""
    for link in file_structure[page_id]:
        child_links += link + " "
    print(child_links)
    print()
