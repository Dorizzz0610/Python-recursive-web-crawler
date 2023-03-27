import mysql.connector
import subprocess

def create_tables():
    connection = mysql.connector.connect(
        host="localhost",
        user="COMP4321",
        password="COMP4321Crawler",
        database="CrawlerDB"
    )

    cursor = connection.cursor()
    # SQL statement to create the keywords table

    names = ["keywords", "relationship", "inverted_index"]
    for name in names:
        cursor.execute("DROP TABLE IF EXISTS " + name)
    connection.commit()

    create_keywords_table = """CREATE TABLE IF NOT EXISTS keywords (
                                page_id INT,
                                word VARCHAR(255) NOT NULL,
                                word_id INT NOT NULL,
                                frequency INT NOT NULL,
                                PRIMARY KEY (page_id, word),
                                FOREIGN KEY (page_id) REFERENCES inverted_index(page_id)
                            )"""

    # SQL statement to create the relationship table
    create_relationship_table = """CREATE TABLE IF NOT EXISTS relationship (
                                page_id INT NOT NULL,
                                relationship TEXT NOT NULL,
                                other_URL TEXT NOT NULL,
                                other_page_id INT,
                                PRIMARY KEY (page_id, other_URL(700)),
                                FOREIGN KEY (page_id) REFERENCES inverted_index(page_id)
                            )"""

    # SQL statement to create the inverted index table
    create_inverted_index_table = """CREATE TABLE IF NOT EXISTS inverted_index (
                                    page_id INT NOT NULL PRIMARY KEY,
                                    url TEXT,
                                    title VARCHAR(255),
                                    last_modified VARCHAR(255),
                                    page_size INT
                                )"""
                                    # FOREIGN KEY (page_id) REFERENCES keywords(page_id),
                                    # FOREIGN KEY (page_id) REFERENCES relationship(page_id)
    cursor.execute(create_inverted_index_table)
    cursor.execute(create_keywords_table)
    cursor.execute(create_relationship_table)
    
    connection.commit()

    # alter_table_keywords = "ALTER TABLE keywords ADD FOREIGN KEY (page_id) REFERENCES inverted_index(page_id)"
    # cursor.execute(alter_table_keywords)
    # alter_table_relationship = "ALTER TABLE relationship ADD FOREIGN KEY (page_id) REFERENCES inverted_index(page_id)"
    # cursor.execute(alter_table_relationship)
    # connection.commit()

    connection.close()




def insert_page(inverted_index, page, url):
    connection = mysql.connector.connect(
        host="localhost",
        user="COMP4321",
        password="COMP4321Crawler",
        database="CrawlerDB"
    )

    cursor =  connection.cursor()

    insert = """
        INSERT INTO inverted_index (page_id, url, title, last_modified, page_size)
        VALUES (%s, %s, %s, %s, %s)
    """

    value = (page.id, url, page.title, page.last_modified, page.size)
    cursor.execute(insert, value)
    connection.commit()
    
    

    # Insert keywords and their frequencies into the keywords table and retrieve the corresponding word_id for each keyword
    insert_keywords = """
        INSERT INTO keywords (page_id, word, frequency, word_id)
        VALUES (%s, %s, %s, %s)
    """
    keywords_insertion = []
    count = 0
    for word in page.keywords.keys():
        keywords_insertion.append([page.id, word, page.keywords[word]["frequency"], page.keywords[word]["word_id"]])
        count += 1
        if(count == 10): break
    cursor.executemany(insert_keywords, keywords_insertion)
    connection.commit()


    # Insert each child url into the children table
    for child_url in page.children:
        if(child_url in inverted_index):
            child_id = inverted_index[child_url]["page_id"]
            cursor.execute("""
                INSERT INTO relationship (page_id, relationship, other_URL, other_page_id) VALUES (%s, %s, %s, %s)
            """, (page.id, "PARENT", child_url, child_id))

        else:
            cursor.execute("""
                INSERT INTO relationship (page_id, relationship, other_URL) VALUES (%s, %s, %s)
            """, (page.id, "PARENT", child_url))


    for parent_url in page.parents:
        parent_id = inverted_index[parent_url]["page_id"]
        cursor.execute("""
            INSERT INTO relationship (page_id, relationship, other_URL, other_page_id) VALUES (%s, %s, %s, %s)
        """, (page.id, "CHILDREN", parent_url, parent_id))
    connection.commit()

    connection.close()



def export_tables():

    config = {
        'user': 'COMP4321',
        'password': 'COMP4321Crawler',
        'database': 'crawlerdb',
        'host': 'localhost'
    }

    # with open('spider result.sql', 'w') as f:     
    #     subprocess.call(["mysqldump", "-u", config['user'], "-p" + config['password'], "-h", config['host'], "--where=1 limit 10000", config['database'], "table"], 
    #       stdout=f)
    
    cmd = ['mysqldump', '-u', config['user'], '-p'+config['password'], '--databases', config['database'], '--result-file', 'spider_result.sql', '--no-create-info']
    # with open('spider result.db', 'wb') as f:
    subprocess.run(cmd)    
