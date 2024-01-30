import dash
import os
import dash_bootstrap_components as dbc
from flask import Flask, request
from flask_babel import Babel, gettext
from dash import Dash, html, dcc
import dash_daq as daq
from dash import callback, dcc, html

# define translator function to use with flask_babel
_ = gettext

def get_locale():
        return request.accept_languages.best_match(LANGUAGES.keys())
    
def get_pages(blacklist='blacklist.txt'):
    try:
        with open(blacklist, r) as bl:
            blacklisted = [l for l in bl.readlines() if (l and (l[0] != '#'))]
    except:
        blacklisted = []
    pages = [page for page in dash.page_registry.values() if page['name'] not in blacklisted]
    return pages

app = Dash('chemistry dashboards', use_pages=True,
           pages_folder='dashboards',
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True
          )

pages = get_pages()
base_dir = os.path.abspath(os.path.dirname(__file__))
translations = ';'.join([os.path.join(base_dir, p["translation"]) for p in pages])
# intialize Flask-babel
babel = Babel(app.server) # app.server is the Flask app inside the dash app.
app.server.config['BABEL_TRANSLATION_DIRECTORIES'] = translations
with app.server.app_context():
    LANGUAGES = {l.language: l.get_language_name() for l in babel.list_translations()}
    babel.init_app(app.server, locale_selector=get_locale)


nav_list = dbc.Nav(
    [
        dbc.NavLink(
            html.Div(page["name"]),
            href=page["path"],
            active="exact",
        )
        for page in pages
    ],
    pills=True,    
)

app.layout = html.Div([nav_list,
              dash.page_container
             ])



if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=5000)
    
    