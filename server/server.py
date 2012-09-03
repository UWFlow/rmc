import flask


app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/profile/')
def profile():
    return flask.render_template('profile.html')

if __name__ == '__main__':
  app.debug = True
  app.run()
