import dash
import dash_bootstrap_components as dbc
from dash import html
from flask_babel import Babel, gettext

# define translator function to use with flask_babel
_ = gettext


def layout():
    title_html = html.H1(_('Chemistry dashboards'))
    
    layout = dbc.Container([
        title_html,
        html.H2('Renato Lombardo')
    ])
    return layout



translation =  __name__.rsplit('.',1)[0].replace('.', '/') + '/translations'

title = 'Home'
subtitle = ''
info = ''
order = 0
translation = translation
dash.register_page(
     __name__,
    path = '/',
    title=title,
    name=title,
    subtitle=subtitle,
    info=info,
    order=order,
    translation = translation
)