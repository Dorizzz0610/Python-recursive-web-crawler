# Recursive-web-crawler

## Index

1. [Overview]
2. [Introducing craweler.py]
3. [Introducing crawler_db.py]
4. [Testing]
5. [Mapping of pages to their keywords]
6. [Mapping of relationship between pages]
7. [Mapping of pages to their information extracted]

## 1. Overview

There are two .py files for the whole project.

- crawler.py
    
    This file handles
    
    1. crawling & extracting the information of the links recursively
    2. storing the extracted data into arrays
    3. exporting the extracted data into spider results.txt
    4. testing program, which is inside the main function
- crawler_db.py
    
    This file handles
    
    1. creating three tables `inverted_index`, `keywords`, and `relationship` in an existed SQL schema `CrawlerDB`, each represents one mapping we will talk about later
    2. inserting the extracted data into the tables
    3. exporting the data to spider results.db

Notice that [crawler.py](http://crawler.py) is the main file and it calls functions in crawler_db.py

## 2. Introducing crawler.py

1. `get_response(url)`:
    - This function takes a URL as input and sends an HTTP GET request to the URL.
    - It returns the HTTP response if the request was successful and `None` if there was an error.
2. `get_head(url)`:
    - This function takes a URL as input and sends an HTTP HEAD request to the URL.
    - It returns the HTTP response headers if the request was successful and `None` if there was an error.
3. `extract(url)`:
    - This function takes a URL as input and extracts the following information from the webpage:
        - Page title
        - Last modified time
        - Page size
        - Keywords and frequencies
        - Children links in the page
    - It returns a `Page` object defined in the same file containing the extracted information. Notice that this object only has attributes yet no method, so it’s actually similar to struct in C++.
4. `store(inverted_index, url, page)`:
    - This function stores the extracted information of a webpage in the inverted index and returns the updated inverted index.
    - If the webpage has already been stored and its last modified time is earlier than the current one, the function does not update the inverted index.
    - How the inverted index is storing the extracted data will be introduced in the later “7. Mapping of pages to their information extracted” part.[
5. `crawl(url, max_pages)`:
    - This function starts crawling the web starting from the given URL and stops after crawling `max_pages` number of pages.
    - It keeps track of the pages that have been crawled and the pages that are waiting to be crawled. If the current link is in the `crawled_list`, then we will skip it - **this handles cyclic cases!**
    - For each page that is crawled, it extracts the information using the `extract()` function and stores it in the inverted index using the `store()` function.
    - Finally, it adds the children links of current link to `crawl_list` in order to continue crawling recursively.
6. `create_txt(inverted_index)`:
    - This function takes the inverted index as input and creates a text file named 'spider result.txt'.
    - It writes the extracted information of each page in the inverted index to the text file in the following format:
        - Page ID
        - Page title
        - URL
        - Last modified time and page size
        - Keywords and frequencies (top 10)
        - Children URLs.

## 3. Introducing crawler_db.py

1. `create_tables()`: 
    
    This function connects to a MySQL database and creates three tables named `keywords`, `relationship`, and `inverted_index`. 
    
    - The `keywords` table stores the words found on each webpage along with their frequency and a word ID.
    - The `relationship` table stores the relationships between webpages such as parent-child relationships.
    - The `inverted_index` table stores metadata about each webpage such as its URL, title, and last modified date.
2. `insert_page(inverted_index, page, url)`: 
    
    The function inserts information about the webpage into the `inverted_index` table, and also inserts information about the keywords found on the page and the relationships between the page and its parent and child pages into the `keywords` and `relationship` tables, respectively.
    
3. `export_tables()`: 
    
    This function exports the data in the `inverted_index`, `keywords`, and `relationship` tables of the MySQL database to a file named `spider_result.sql`. It uses the `mysqldump` command to generate the SQL statements needed to recreate the tables and insert the data into them, and writes these statements to the file.
    

## 4. Testing

The testing process is done in main() of crawler.py.

You can set the base link you want to crawl and the number of links you want to crawl recursively.

```python
url = "https://www.cse.ust.hk"
MAX_PAGES = 30
```

Then, we use your parameters to call crawl() and get the resulting inverted index.

```python
inverted_index = crawl(url, MAX_PAGES)
```

In order to generate spider result.txt, we call:

```python
create_txt(inverted_index)
```

Also, in order to generate spider result.db in a MySQL database form, we call:

```python
crawler_db.export_tables()
```

## 5. Mapping of pages to their keywords

- Python
    
    When extracting keywords in a page, create a dictionary whose:
    
    - key: word, a String
    - value:
        1. word_id, assigned when being extracted one by one
        2. frequency, increment 1 each time when we get this word
- MySQL
    
    We use a table `keywords`.
    
    1. Structure of the table
        
        For every row, we have 
        
        ```sql
        page_id INT,
        word VARCHAR(255) NOT NULL,
        word_id INT NOT NULL AUTO_INCREMENT,
        frequency INT NOT NULL,
        PRIMARY KEY (page_id, word),
        FOREIGN KEY (page_id) REFERENCES inverted_index(page_id)
        ```
        
        Each row is a page_id→word & word_id mapping.
        
        So we can based on the page_id to check all the keywords in this link.
        
    2. Query data from the table
        - query all the keywords and their word_id in a specific page
        
        ```sql
        SELECT word, word_id
        FROM keywords
        WHERE page_id = i;
        ```
        

## 6. Mapping of relationship between pages

e.g. parents & children

- Python
    
    When extracting children links in a page, create a dictionary whose:
    
    - key:
        
        “children”, a string
        
    - value:
        
        children link URL, a String
        
- MySQL
    
    We use a table `relationship`.
    
    1. Structure of the table
        
        For every row, we have 
        
        ```sql
        page_id INT NOT NULL,
        relationship TEXT NOT NULL,
        other_URL TEXT NOT NULL,
        other_page_id INT,
        PRIMARY KEY (page_id, other_URL(700)),
        FOREIGN KEY (page_id) REFERENCES inverted_index(page_id)
        ```
        
        e.g. 
        
        For a row `10 CHILDREN [www.google.com](http://www.google.com) 3`
        
        We can interpret as: link with `page_id`=10 is the children link of [www.google.com](http://www.google.com) with `page_id`=3.
        
        For a row `7 PARENT [www.bing.com](http://www.bing.com) NULL`
        
        We can interpret as: link with `page_id`=7 is the parent link of [www.bing.com](http://www.bing.com) without a `page_id`. (this means that this link haven’t been crawled by us)
        
        *Note that parent links are the links already crawled by us, so they all have been assigned with unique `page_id`.* ****Therefore, we can just include their page_id here without the URL, and retrieve their URL in `inverted_index` table if needed.
        
        *However, the children links are possibly not crawled by us, so we need to add their URLs here, in case their `page_id = NULL`.*
        
    1. Query data from the table
    - When we want to query all the children of a page_id, just do
        
        ```sql
        SELECT other_URL 
        FROM relationship
        WHERE relationship = 'CHILDREN' 
        AND page_id = <target_page_id>;
        ```
        
    - When we want to query all the parents of a page_id
        
        ```sql
        SELECT other_URL 
        FROM relationship
        WHERE relationship = 'PARENT' 
        AND other_page_id = <target_page_id>;
        ```
        

## 7. Mapping of pages to their information extracted

- Python
    
    Inverted index: a dictionary, whose:
    
    - key: url
    - value: a dictionary, whose:
        - key: strings of attribute
            1. “page_id”
            2. “title”
            3. “last_modified”
            4. “page_size”
            5. “keywords”
            6. “children”
        - value: value of attribute, which all correspond to the attributes of the class Page defined in the .py file
    
    By iterating the list `children` and directly get each element’s feature `id` we are able to return the page-IDs of the children pages given the page-ID of the parent page and vice versa.

- MySQL
    
    We use a table `inverted_index`.
    
    1. Structure of the table
        
        For every row, we have 
        
        ```sql
        page_id INT NOT NULL PRIMARY KEY,
        url TEXT,
        title VARCHAR(255),
        last_modified VARCHAR(255),
        page_size INT,
        FOREIGN KEY (page_id) REFERENCES keywords(page_id),
        FOREIGN KEY (page_id) REFERENCES relationship(page_id)
        ```
        
    2. Query all the extracted data of a specific page_if from table
        
        ```sql
        SELECT *
        FROM inverted_index
        WHERE page_id = i;
        ```
