import dash
import dash_bootstrap_components as dbc
from dash import html
from flask_babel import Babel, gettext

# define translator function to use with flask_babel
_ = gettext


home_page = 'https://www.unipa.it/persone/docenti/l/renato.lombardo'
uni_home_page = 'https://wwww.unipa.it'
source = 'https://github.com/renato-lombardo/physchem-dashboards'
license =  'https://www.gnu.org/licenses/agpl-3.0.en.html'

def layout():
    title_html = html.H1('Chemistry dashboards')
    description = html.H3(_('A small set of interactive dashboards to show the behavior of some models in chemistry'))
        
    layout = dbc.Container([
        title_html,
        description,
        html.H4(html.A('Renato Lombardo', href = home_page, target="_blank")),
        html.H4(html.A(_('University of Palermo'), href=uni_home_page, target="_blank")),
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