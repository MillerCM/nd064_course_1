import logging
import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from sys import stderr, stdout
from werkzeug.exceptions import abort

# Define globals
# I am assuming that the intent is to track & increment the number of times that DB connections have been
# used since the last deploy of the app, rather than the number of active connections (since the prompt did
# not specify active connections).
DB_CONNECTION_COUNT = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row

    global DB_CONNECTION_COUNT
    DB_CONNECTION_COUNT += 1
    
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Function to get total number of post entries from the posts table
def get_number_of_posts():
    connection = get_db_connection()
    count_result = connection.execute('SELECT count(*) FROM posts').fetchone()
    connection.close()
    return count_result[0]

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.warning("Non-existent post id %d", post_id)
        return render_template('404.html'), 404
    else:
        # post index 2 is the article title
        app.logger.info("Article '%s' retrieved!", post[2])
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("Page 'About Us' retrieved!")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info("Article '%s' was added!", title)
            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response = json.dumps({"result": "OK - healthy"}),
            status = 200,
            mimetype = 'application/json'
    )
    return response

@app.route('/metrics')
def metrics():
    # Note: Fetching the post count from the database will increment the DB_CONNECTION_COUNT
    num_posts = get_number_of_posts()
    # I considered adding an arg to to get_db_connection to exclude connections originating from accesses 
    # to the /metrics from the connection count, but determined that it would be better include these given
    # that they are database connections and could be useful to detect a rogue internal process that inadvertently
    # affects site availability
    global DB_CONNECTION_COUNT
    response = app.response_class(
            response = json.dumps({"db_connection_count": DB_CONNECTION_COUNT, "post_count": num_posts}),
            status = 200,
            mimetype = 'application/json'
    )
    return response

# start the application on port 3111
if __name__ == "__main__":
    # the timestamp is already part of the default config, so I did not modify the format
    logging.basicConfig(
        format="%(asctime)s:%(name)s:%(levelname)s: %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S %z",
        level=logging.DEBUG, 
        handlers=[logging.StreamHandler(stderr), logging.StreamHandler(stdout)]
    )
    app.run(host='0.0.0.0', port='3111')