import numpy as np
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
import re
from dash import callback, dcc, html
from dash import dash_table
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from dash.dash_table.Format import Format, Scheme
from flask import Flask, request
from flask_babel import Babel, gettext
from model import population
from plotly.subplots import make_subplots

# define translator function
_ = gettext


#########################
# Dashboard information #
#########################
title = "Boltzmann distribution"
subtitle = "explore how each distribution changes on changing the parameters"
info = r'''
        **Boltzmann distribution** describes how $N$ molecules are distributed on different energy levels, depending on temperature. The fraction of molecules with energi $E_1$ is:  
        
        $$\frac{N_1}{N} = \frac{e^{-\frac{E_1}{kT}}}{Q}$$  
        
        Where $Q$ is the **molecular partition function**:  
        
        $$Q = \sum_{i} e^{-\frac{E_i}{kT}}$$  
        
        It is a _normalization factor_ that ensures that the total probability will be 1.
        '''


##################################
# common variables and utilities #
##################################

e_max_r = [0.01, 5] # energy range
T_r = [1, 1e4] # temperature range
n_r = [2, 25] # number of levels range


#######################################
# set up general layout and callbacks #
#######################################

def header():
    title_html = html.H1(_(title), id='title')
    subtitle_html = html.P(_(subtitle), id='subtitle')
    info_button = dbc.Button(id='info-button', n_clicks=0, children='more info')
    # a text area that support mathjax and Latex for equations
    info_text = dcc.Markdown('   ', mathjax=True, id='info-text')
    # put button and text area togheter
    title_col = dbc.Col(dbc.Container([title_html, subtitle_html]), width='auto')
    info_col = dbc.Col(dbc.Container([info_text, info_button]), width='auto')
    #header = dbc.Row([title_col, info_col])
    return dbc.Row([title_col, info_col])


@callback([Output('title', 'children'),
           Output('subtitle', 'children')
           ],
          [Input('title', 'children'),
           Input('subtitle', 'children')
          ])
def setup_language_general(*messages):
    return [_(m) for m in messages]


@callback([Output('info-button', 'children'),
               Output('info-text', 'children')],
              Input('info-button', 'n_clicks')
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

##########################
# set up specific layout #
##########################

def panel_factory(uid):
    '''
    create a panel with controls and table on the left and plot on the right
    
    Parameters
    ----------
    uid : int
        unique ID of the item to create
        
    Return
    ------
    panel : object
        panel with controls and table on the left and plot on the right
    '''
    left = dbc.Col(controls_factory(uid), xl=4)
    right = dbc.Col(dcc.Graph(id={'type': 'B-plot', 'uid': uid}), xl=8)
    panel = dbc.Container(dbc.Row([left, right], align='center'), id={'type': 'panel', 'uid': uid}, fluid=True)
    return panel

                          
def controls_factory(uid):
    '''
    generate a container with all the controls and a table
    
    Parameters
    ----------
    uid : int
        unique ID of the item to create
        
    Return
    ------
    controls : object
        controls container
    '''   
    e_max_input = dbc.Row([dbc.Col(dbc.Label(_('Max energy (eV)'), id={'type': 'e-max-label', 'uid': uid})),
                        dbc.Col(dbc.Input(id={'type': 'e-max-input', 'uid': uid}, type='number',
                                         min=e_max_r[0], max=e_max_r[1], step=0.01, value=0.1))
                         ])
    n_input = dbc.Row([dbc.Col(dbc.Label(_('n levels'), id={'type': 'n-label', 'uid': uid})),
                        dbc.Col(dbc.Input(id={'type': 'n-input', 'uid': uid}, type='number',
                                         min=n_r[0], max=n_r[1], value=5))
                        ])
    t_input = dbc.Row([dbc.Col(dbc.Label(_('temperature (K)'), id={'type': 't-label', 'uid': uid})),
                        dbc.Col(dbc.Input(id={'type': 't-input', 'uid': uid}, type='number',
                                         min=T_r[0], max=T_r[1], value=298))
                        ])
    delete_button = dbc.Col(dbc.Button(_('delete'), id={'type': 'delete-button', 'uid': uid}), width='auto')
    input_row = dbc.Container([
        e_max_input,
        n_input,
        t_input
    ])
    data_table = dash_table.DataTable(
        id = {'type': 'data-table', 'uid': uid},
        columns = [
                {'name': _('energy'), 'id': 'energy', 'type': 'numeric', 'format': Format(precision=2, scheme=Scheme.fixed)},
                {'name': _('pop fract'), 'id': 'population', 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)}
            ],
        data = [],
        editable = True,
        export_format='csv',
        page_action='none',
        style_table={'height': '300px', 'overflowY': 'auto'}
        )
    controls = dbc.Container([dbc.Row([delete_button]), input_row, data_table], id={'type': 'card', 'uid': uid})
    return controls


def add_to_container(item, container_list, max_col=2, col_props={}, row_props={}):
    '''
    add an item to a container (such as a Panel, etc.) in a rows, columns structure
    
    Parameters:
    item : object
        the item to add
    container : object
        the container
    max_col : int
        maximum number of columns per row
    col_props : dict
        column properties
    row_props : dict
        row properties
    '''
    # create a column with the item inside and the required properties
    new_col = dbc.Col([item], **col_props)
    if not container_list: # add the first row
        return [dbc.Row([new_col], **row_props)]
    # if the last row is full
    row = container_list[-1]
    if isinstance(row, dbc.Row):
        n_cols = len(row.children)
    else:
        n_cols = len(row['props']['children'])
    if n_cols==max_col:
        new_row = dbc.Row([new_col], **row_props)
        return container_list + [new_row]
    else:
        # add the column to the row
        if isinstance(row, dbc.Row):
            row.children += [new_col]
        else:
            row['props']['children'] += [new_col]
        container_list[-1] = row
        return container_list


def remove_from_container(uid, container_list):
    '''
    Remove item from container
    
    Parameters
    ----------
    uid : int
        unique ID of the item to remove
    container : object
        container
    max_col : int
        maximum number of columns per row
    
    '''
    new_container_list = []
    for row in container_list:
        for col in row['props']['children']:
            item = col['props']['children'][0]
            if item['props']['id']['uid'] != uid:
                new_container_list = add_to_container(item, new_container_list)
    return new_container_list


def update_table(E, pop):
    '''
    remove energy E and sort table
    '''
    # sort list on E values
    data = [{'energy': e, 'population': p } for e, p in sorted(zip(E, pop.magnitude))]
    return data


add_button = dbc.Button(_('Add plot'), id='add-button', style={'margin-bottom':5})
panels_container = dbc.Container([], id='panels-container', fluid=True)
layout = dbc.Container([
        header(),
        html.Hr(),
        dbc.Row([dbc.Col(add_button, xl=6, align='left')]),
        dbc.Row([panels_container], align='left')
    ],
    id='layout',
    fluid=True
)

######################
# specific callbacks #
######################

@callback([Output('add-button', 'children')],
          [Input('add-button', 'children')])
def setup_language_specific(*messages):
    return [_(m) for m in messages]


@callback(Output('panels-container', 'children'),
              [Input('add-button', 'n_clicks'),
              Input({'type':'delete-button', 'uid': ALL}, 'n_clicks')],
              State('panels-container', 'children')
             )
def update_panels_container(add_n_clicks, clear_n_clicks, panels_container_list):
    '''update container adding or removing controls as required'''
    ctx = dash.callback_context # this is needed to know which button has been pushed
    trigger = ctx.triggered[0]
    if 'add-button' in trigger['prop_id']: # add a new panel
        uid = add_n_clicks # unique id 
        new_panel = panel_factory(uid=uid)
        return add_to_container(new_panel, panels_container_list)
    else: # some delete button has been pushed
        match = re.search(r'"uid":(\d+)',trigger['prop_id'])
        if match:
            uid = int(match.group(1)) # uid of the card
            return remove_from_container(uid, panels_container_list)
        else:
            raise PreventUpdate # needed when app starts
            

# this is the most important function
@callback([
               Output({'type': 'B-plot', 'uid': MATCH}, 'figure'),
               Output({'type': 'data-table', 'uid': MATCH}, 'data')
              ],
              [
               Input({'type': 'e-max-input', 'uid': MATCH}, 'value'),
               Input({'type': 'n-input', 'uid': MATCH}, 'value'),
               Input({'type': 't-input', 'uid': MATCH}, 'value')
              ]
             )
def update_plot_table(e_max, n, T):
    if None in (e_max, n, T): # values outside ranges 
        return go.Figure(), []
    for val, vrange in zip((e_max, n, T), (e_max_r, n_r, T_r)):
        if (val<vrange[0]) or (val>vrange[1]):
            return go.Figure(), []
    E = np.linspace(0, e_max, n)
    pop = population(E, T)
    fig = go.Figure(go.Bar(
            x=pop.magnitude,
            y=E,
            orientation='h'))
    fig.update_layout(xaxis_title=_('population fraction'))
    fig.update_yaxes(tickmode='array',  tickvals=E, ticktext=[_('level')+ f' {i} ' for i in range(n)])
    table_data = update_table(E, pop)
    return fig, table_data


if __name__ == '__main__': # use as a standalone dash app
    ####################
    # Initilialize app #
    ####################
    # create the app
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    def get_locale():
        return request.accept_languages.best_match(LANGUAGES.keys())
    
    # intialize Flask-babel
    babel = Babel(app.server) # app.server is the Flask app inside the dash app.
    with app.server.app_context():
        LANGUAGES = {l.language: l.get_language_name() for l in babel.list_translations()}
        babel.init_app(app.server, locale_selector=get_locale)
    app.layout = layout
    app.run_server(debug=True, host='0.0.0.0', port=5000)
else: # use as a page in a dash multipage app
    dash.register_page(
        __name__,
        path=__name__,
        title=title,
        name=title,
        subtitle=subtitle,
        info=info,
        order=3
)

