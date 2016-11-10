from flask import Flask, url_for, send_from_directory
from dsm_genres import *

app_explorer = Flask(__name__,static_url_path='/data/')

@app_explorer.route('/data/<path:path>')
def send_js(path):
    return send_from_directory('data', path)

app_explorer.register_blueprint(genre)


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app_explorer.jinja_env.globals['url_for_other_page'] = url_for_other_page

if __name__ == '__main__':
    app_explorer.run()
