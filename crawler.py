import os
import requests
from urllib import request, error, parse
from bs4 import BeautifulSoup



# TODO: Define the database to store the indexed pages


class Page:
    def __init__(self, id, title, last_modified, size, keywords, children, parents):
        self.id = id
        self.title = title
        self.last_modified = last_modified
        self.size = size
        self.keywords = keywords
        self.children = children
        self.parents = parents



# Get the response of HTTP request
def get_response(url):
    try:
        response = requests.get(url)
        return response
    except:
        return None

# Get the head of HTTP request
def get_head(url):
    try:
        head = requests.head(url)
        return head
    except:
        return None
    

# Extract the HTML content of the URL
def extract(url):
    response = get_response(url)
    response = response.text
    page = BeautifulSoup(response, 'html.parser')

    # Page title
    if(page.title):
        title = page.title.string.strip()
    else:
        title = ""

    # Last modified time
    head = get_head(url)
    last_modified = head.headers.get('Last-Modified')
    if last_modified is not None and last_modified > "":
        last_modified = last_modified
    else:
        last_modified = ""

    # Page size
    size = len(response)

    # Keywords and frequencies
    keywords = {}
    word_id = 0
    for word in page.get_text().split():
        word = word.strip().lower()
        if word in keywords:
            keywords[word]["frequency"] += 1
        else:
            keywords[word] = {}
            keywords[word]["frequency"] = 1
            keywords[word]["word_id"] = word_id
            word_id += 1

    # Children links in the page
    children = []
    for child in page.find_all('a'):
        child_link = child.get('href')
        if child_link and child_link.startswith('http'):
            if child_link not in children and child_link != url:
                children.append(child.get('href'))
    parents = []
    result = Page(-1, title, last_modified, size, keywords, children, parents) # -1 is just a placeholder
    return result


def store(inverted_index, url, page):
    if url not in inverted_index:
        inverted_index[url] = {
            "page_id": page.id,
            "title": page.title,
            "last_modified": page.last_modified,
            "page_size": page.size,
            "keywords": page.keywords,
            "children": page.children,
            "parents": page.parents
        }
    else:
        if "last_modified" not in inverted_index[url]:
            inverted_index[url] = {
                "page_id": page.id,
                "title": page.title,
                "last_modified": page.last_modified,
                "page_size": page.size,
                "keywords": page.keywords,
                "children": page.children,
                "parents": page.parents
            }
        elif "last_modified" in inverted_index[url] and inverted_index[url]["last_modified"] != "" and page.last_modified > inverted_index[url]["last_modified"]:
            inverted_index[url] = {
                "page_id": page.id,
                "title": page.title,
                "last_modified": page.last_modified,
                "page_size": page.size,
                "keywords": page.keywords,
                "children": page.children,
                "parents": page.parents
            }
    
    return inverted_index

def anti_cyclic(inverted_index):
    visited_pages = set()
    for url in inverted_index:
        stack = [url]
        while(stack):
            current_url = stack.pop()
            if current_url in visited_pages:
                del inverted_index[current_url]
            else:
                visited_pages.add(current_url)
                stack.extend(inverted_index[current_url])
    return inverted_index


def crawl(url, max_pages):
    crawl_list = [url]
    crawled_list = []
    count = 0

    inverted_index = {url: {}} #store parent->chidren

    while crawl_list and count < max_pages:
        current_url = crawl_list.pop(0)
        if current_url in crawled_list:
            continue
        if(get_response(current_url)):
            current_page = extract(current_url)
            current_page.id = count
            print("finish extracting " + current_url)
            print(current_page.id)
            print(current_page.title)
            print(current_page.size)
            print(current_page.keywords)
            inverted_index[current_url] = {}
            inverted_index[current_url]["children"] = current_page.children
            for child in current_page.children:
                if child not in crawled_list and child not in crawl_list: #avoid cyclic?
                    crawl_list.append(child)
                    #inverted_index[child] = {}
            crawled_list.append(current_url)
            count += 1
            inverted_index = store(inverted_index, current_url, current_page)

    for url in inverted_index:  
        for child in inverted_index[url]["children"]:
            if child in inverted_index.keys():
                inverted_index[child]["parents"].append(url)
    return inverted_index

def print_pages(inverted_index):
    for url in inverted_index:
        print("URL: " + url)
        print("Title: " + inverted_index[url]["title"])
        print("Last modified: " + inverted_index[url]["last_modified"])
        print("Page size: " + str(inverted_index[url]["page_size"]))
        keys = list(inverted_index[url]["keywords"].keys())
        sliced_keys = keys[:10]
        sliced_keywords = {key: inverted_index[url]["keywords"][key] for key in sliced_keys}
        for key, value in sliced_keywords.items():
            print("\"" + key + "\"" + "(Word ID: " + str(value["word_id"]) + "): " + str(value["frequency"]) + "; ")
        for child in inverted_index[url]["children"]:
            if child in inverted_index:
                print("Child: " + str(inverted_index[child]['page_id']))
        print("")

def create_txt(inverted_index):
    with open('spider result.txt', 'w') as file:
        for url in inverted_index:
            file.write("Page ID: " + str(inverted_index[url]["page_id"]) + "\n")
            file.write("Page title: " + inverted_index[url]["title"] + "\n")
            file.write("URL: " + url + "\n")
            file.write("Last modified: " + inverted_index[url]["last_modified"] + "    Page size: " + str(inverted_index[url]["page_size"]) + "\n")
            keys = list(inverted_index[url]["keywords"].keys())
            sliced_keys = keys[:10]
            sliced_keywords = {key: inverted_index[url]["keywords"][key] for key in sliced_keys}
            file.write("Keywords: ")
            for key, value in sliced_keywords.items():
                file.write("\"" + key + "\"" + "(Word ID: " + str(value["word_id"]) + "): " + str(value["frequency"]) + "; ")
            file.write("\n")
            count = 1
            for child in inverted_index[url]["children"]:
                if child in inverted_index.keys() and "page_id" in inverted_index[child].keys():
                    file.write("Child Link " + str(count) + ": " + child + " (page ID: " + str(inverted_index[child]["page_id"]) + ")")
                else:
                    file.write("Child Link " + str(count) + ": " + child)
                count += 1
                file.write("\n")
            file.write("\n")
            count = 1
            for parent in inverted_index[url]["parents"]:
                if parent in inverted_index.keys() and "page_id" in inverted_index[parent].keys():
                    file.write("Parent Link " + str(count) + ": " + parent + " (page ID: " + str(inverted_index[parent]["page_id"]) + ")\n")
                    count += 1
            file.write("\n")
            file.write("-------------------------------------------\n")


def main():
    url = "https://www.cse.ust.hk"
    MAX_PAGES = 30
    inverted_index = crawl(url, MAX_PAGES)
    #inverted_index = anti_cyclic(inverted_index)
    create_txt(inverted_index)
    #print_pages(inverted_index)
    

if __name__ == "__main__":
    main()
