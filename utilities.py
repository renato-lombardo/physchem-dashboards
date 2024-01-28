import dash_bootstrap_components as dbc
import inspect
import os
from dash import callback, dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from flask_babel import Babel, gettext
# define translator function to use with flask_babel
_ = gettext

def _id(string, _prefix=''):
    '''add unique string to each id, in order to avoid collision with other elemets of the global dashboard'''
    if not _prefix:
        if __name__ == '__main__':
            return string
        caller = inspect.stack()[1]
        prefix = os.path.basename(caller.filename).split('.')[0]
    return prefix+'-'+string
    
#######################################
# set up general layout and callbacks #
#######################################

def common_setup(title, subtitle, info):
    caller = inspect.stack()[1]
    prefix = os.path.basename(caller.filename).split('.')[0]
    title_id = prefix + '-title'
    subtitle_id = prefix + '-subtitle'
    info_button_id = prefix +  '-info_button'
    info_text_id = prefix + '-info_text'

    def header():
        title_html = html.H1(_(title), id=title_id)
        subtitle_html = html.P(_(subtitle), id=subtitle_id)
        info_button = dbc.Button(id=info_button_id, n_clicks=0, children='more info')
        # a text area that support mathjax and Latex for equations
        info_text = dcc.Markdown('   ', mathjax=True, id=info_text_id)
        # put button and text area togheter
        title_col = dbc.Col(dbc.Container([title_html, subtitle_html]), width='auto')
        info_col = dbc.Col(dbc.Container([info_text, info_button]), width='auto')
        #header = dbc.Row([title_col, info_col])
        return dbc.Row([title_col, info_col])
    
    @callback([Output(title_id, 'children'),
               Output(subtitle_id, 'children')
               ],
              [Input(title_id, 'children'),
               Input(subtitle_id, 'children')
              ])
    def setup_language_general(*messages):
        return [_(m) for m in messages]
    
    
    @callback([Output(info_button_id, 'children'),
                   Output(info_text_id, 'children')],
                  Input(info_button_id, 'n_clicks')
                 )
    def show_info(n_clicks):
        '''show a short information about the model '''
        if n_clicks%2: # button pressed for an uneven number of times
            text = _(info)
            button_text = _('less info') # change the label
        else: # clicked again after showing, means hide the info
            text = '   '
            button_text = _('more info')
        return button_text, text
    return header, setup_language_general, show_info