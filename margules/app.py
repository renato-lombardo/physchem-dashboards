import numpy as np
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.express as px
import plotly.graph_objs as go
import re
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from flask import Flask, request
from flask_babel import Babel, gettext
from model import DG_mix, DS_mix, DH_mix, R

# define translator function
_ = gettext

colors = px.colors.qualitative.Plotly

###################################
# Initilialize app with languages #
###################################
external_scripts = []
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], external_scripts=external_scripts)
server = app.server
babel = Babel(app.server)
LANGUAGES = {l.language: l.get_language_name() for l in babel.list_translations()}

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())

app.config.update({'external_scripts': [f'https://cdn.plot.ly/plotly-locale-{lan}-latest.js' for lan in LANGUAGES]})
app.config.update({'title': _('Regular solutions')})

###########################
# dash element definition #
###########################

add_button = dbc.Button(_('Add plot'), id='add-button', style={'margin-bottom':5})
controls_container = dbc.Container([], id='controls-container', fluid=True)
plot = dcc.Graph(id='plot', style={'height': '80vh'})
title = html.H1(_("Regular solutions"), id='title')
subtitle = html.P(_("explore how miscibilty changes on changing the enthalpy of mixing"), id='subtitle')
info_button = dbc.Button(id='info-button', n_clicks=0, children='More info')
info_text = dcc.Markdown('   ', mathjax=True, id='info-text')
# put button and text area togheter
info = dbc.Container([info_text, info_button])

title_col = dbc.Col(dbc.Container([title, subtitle]), width='auto')
info_col = dbc.Col(dbc.Container([info_text, info_button]), width='auto')
header = dbc.Row([title_col, info_col])
# Layout of the app with all the widgets
app.layout = dbc.Container([
    header,
    html.Hr(),
    add_button,
    dbc.Row([
        dbc.Col(controls_container, align='left'),
        dbc.Col([plot], xl=8, align='left')
        ])
    ],
    fluid=True
    )

                         
def controls_factory(uid):
    '''
    generate a container with all the controls
    
    Parameters
    ----------
    uid : int
        unique ID of the item to create
        
    Return
    ------
    controls : object
        controls container
    '''   

    beta_input = dbc.Row([
        dbc.Col(dbc.Label('\u03B2 (kJ/mol)')),
        dbc.Col(dbc.Input(value=0,
                  step = 0.1,
                  type='number',
                  id={'type': 'beta-input', 'uid': uid}
                 ))]
    )
    
    t_input = dbc.Row([
        dbc.Col(dbc.Label('T (K)')),
        dbc.Col(dbc.Input(value=298,
                  min = 5,
                  step = 1,
                  type='number',
                  id={'type': 't-input', 'uid': uid}
                  ))]
    )
    
    inputs = dbc.Container([beta_input, t_input], fluid=True)
    
    DG_switch = daq.BooleanSwitch(id={'type':'DG-switch', 'uid':uid},
                                                   on=True,
                                                   label= '\u0394G',
                                                   labelPosition='right')
    
    DS_switch = daq.BooleanSwitch(id={'type':'DS-switch', 'uid':uid},
                                                   on=False,
                                                   label='T\u0394S',
                                                   labelPosition='right')
    
    DH_switch = daq.BooleanSwitch(id={'type':'DH-switch', 'uid':uid},
                                                   on=False,
                                                   label='\u0394H',
                                                   labelPosition='right')
    
    minima_switch = daq.BooleanSwitch(id={'type':'minima-switch', 'uid':uid},
                                                   on=True,
                                                   label=_('Minima'),
                                                   labelPosition='right')
    
    switches = dbc.Container([DG_switch, DS_switch, DH_switch, minima_switch], fluid=True)
    
    x1_min = dbc.Label('\u03C7\u2081 min = --', id=dict(type='x1-min', uid=uid))
    x1_max = dbc.Label('\u03C7\u2081 max = --', id=dict(type='x1-max', uid=uid))
    delete_button = dbc.Col(dbc.Button(_('delete'), id={'type': 'delete-button', 'uid': uid}), width='auto')
    bottom = dbc.Row([dbc.Col(delete_button, width=4), dbc.Col(x1_min, width=4), dbc.Col(x1_max, width=4)], justify='center')
    controls = dbc.Card([dbc.Row([dbc.Col(inputs, width=8), dbc.Col(switches)]),html.Hr(), bottom],
                            id={'type': 'controls-card', 'uid': uid}, style={'margin-bottom':5})
    return controls

#############
# Callbacks #
#############
@app.callback([Output('info-button', 'children'),
               Output('info-text', 'children')],
              Input('info-button', 'n_clicks')
             )
def show_info(n_clicks):
    if n_clicks%2: #uneven number
        text = _(r'''
        Mixing two liquids 1 and 2 requires that the **Gibbs Energy of mixing** must be negative:  
       
        $$\Delta_{mix} G  = nRT(\chi_1 ln \chi_1 + \chi_2 ln \chi_2) + \Delta_{mix} H$$

        For **regular solutions** the enthalpy of mixing can be expressed in terms of the molar fractions and a specific parameter $\beta$: 
        
        $$\Delta_{mix} H  =  n \beta\cdot\chi_1\cdot\chi_2$$
        
        So that it is posssible to use **Margules equation** to calculate $\Delta_{mix}G$:  
        
        $$\Delta_{mix} G  = nRT(\chi_1 ln \chi_1 + \chi_2 ln \chi_2) + n \beta\cdot\chi_1\cdot\chi_2$$        

        On increasing the parameter $\beta$, the enthalpy of mixing increases and the solubility of 1 in 2 decreases. When $\frac{\beta}{RT}>2$ **demixing** is observed with the
        formation of two minima in the curve that correspond to two different phases.
        ''')
        button_text = _('less info')
    else:
        text = '   '
        button_text = _('more info')
    return button_text, text

@app.callback(Output('controls-container', 'children'),
              [Input('add-button', 'n_clicks'),
               Input({'type':'delete-button', 'uid': ALL}, 'n_clicks')],
              State('controls-container', 'children')
             )
def update_controls_container(add_n_clicks, clear_n_clicks, controls_container_list):
    '''update container adding or removing controls as required'''
    ctx = dash.callback_context # this is needed to know which button has been pushed
    trigger = ctx.triggered[0]
    if 'add-button' in trigger['prop_id']: # add a new panel
        uid = add_n_clicks # unique id 
        new_controls = controls_factory(uid=uid)
        return controls_container_list+[new_controls]
    else: # some delete button has been pushed
        match = re.search(r'"uid":(\d+)',trigger['prop_id'])
        if match:
            uid = int(match.group(1)) # uid of the card
            return [c for c in controls_container_list if c['props']['id']['uid'] != uid]
        else:
            raise PreventUpdate # needed when app starts
            

# this is the most important function
@app.callback([Output('plot', 'figure'),
               Output({'type':'controls-card', 'uid': ALL}, 'style'),
               Output({'type':'x1-min', 'uid': ALL}, 'children'),
               Output({'type':'x1-max', 'uid': ALL}, 'children')],
              [Input({'type':'beta-input', 'uid': ALL}, 'value'),
               Input({'type':'t-input', 'uid': ALL}, 'value'),
               Input({'type':'DG-switch', 'uid': ALL}, 'on'),
               Input({'type':'DS-switch', 'uid': ALL}, 'on'),
               Input({'type':'DH-switch', 'uid': ALL}, 'on'),
               Input({'type':'minima-switch', 'uid': ALL}, 'on')],
               [State({'type':'controls-card', 'uid': ALL}, 'style')]
             )
def update_plot(beta_list, T_list, DG_list, DS_list, DH_list, minima_list, styles):
    data = []
    new_styles = []
    x1_min_values = []
    x1_max_values = []
    for i, (beta, DG, DS, DH, minima, T, st) in enumerate(zip(beta_list, DG_list, DS_list, DH_list, minima_list, T_list, styles)):
        if None in (beta, T): # values outside ranges 
            return go.Figure(), {}
        color = colors[i%len(colors)]
        st['border-color'] = color
        new_styles.append(st)
        beta = beta*1000 # convert to J/mol
        alpha = beta/(R*T)
        if DG:
            x, y = DG_mix(beta, T)
            y = y*0.001 # kJ/mol
            data.append(go.Scatter(x=x, y=y, mode='lines', line=dict(color=color), name=f'\u0394G: \u03B2 {beta/1000:.1f} kJ/mol, {T} K')) 
            if alpha>2:
                idx = np.argsort(y)[:2]
            else:
                idx = [int(len(x)/2)]
            x1_min_values.append(f'\u03C7\u2081 min = {x[idx][-1]:.3f}')
            x1_max_values.append(f'\u03C7\u2081 max = {x[idx][0]:.3f}')
            if minima:
                data.append(go.Scatter(x=x[idx], y=y[idx], mode='markers', marker_color='black', marker_symbol='circle-open', marker_size=10, showlegend=False))
        else:
            x1_min_values.append('\u03C7\u2081 min = --')
            x1_max_values.append('\u03C7\u2081 max = --')
            
        if DS:
            x, y = DS_mix(T)
            y = y*0.001 # kJ/mol
            data.append(go.Scatter(x=x, y=T*y, mode='lines', line=dict(color=color, dash='dash'), name=f'T\u0394S: \u03B2 {beta/1000:.1f} kJ/mol, {T} K'))
        if DH:
            x, y = DH_mix(beta, T)
            y = y*0.001 # kJ/mol
            data.append(go.Scatter(x=x, y=y, mode='lines', line=dict(color=color, dash='dashdot'), name=f'\u0394H: \u03B2 {beta/1000:.1f} kJ/mol, {T} K'))
        
    layout = {'xaxis': {'title': _('\u03C7\u2081'), 'range': (0,1)}, 'yaxis': {'title': _('Energy kJ/mol')}}
    return go.Figure(data=data, layout=layout), new_styles, x1_min_values, x1_max_values

@app.callback([
               Output('add-button', 'children'),
               Output('title', 'children'),
               Output('subtitle', 'children'),
              ],
              [Input('add-button', 'children'),
               Input('title', 'children'),
               Input('subtitle', 'children'),
              ])
def setup_language(*messages):
    return [_(m) for m in messages]


if __name__ == '__main__':
    app.run_server(debug=True)
