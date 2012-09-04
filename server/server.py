import flask


app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.render_template('index_page.html')

@app.route('/profile')
def profile():
    return flask.render_template('profile_page.html')

if __name__ == '__main__':
  app.debug = True
  app.run()
