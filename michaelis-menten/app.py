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
from model import michaelis_menten

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



external_scripts = [f'https://cdn.plot.ly/plotly-locale-{lan}-latest.js' for lan in LANGUAGES]

app.config.update({'external_scripts': external_scripts })
app.config.update({'title': _('Michaelis-Menten kinetics')})


###########################
# dash element definition #
###########################

def controls_card_factory(uid=None):
    KM_input = dbc.Col(dbc.Row([
        dbc.Col([html.H5(['K',html.Sub('M'), ' mol/L'])]),
        dbc.Col(dbc.Input(value=0.015,
                          step = 0.001,
                          type='number',
                          min=0.001,
                          id={'type': 'KM-input', 'uid': uid}
                         ))
    ]))
                                      
    k2_input = dbc.Col(dbc.Row([
        dbc.Col([html.H5(['k',html.Sub('2'), ' mol/L'])]),
        dbc.Col(dbc.Input(value=0.14,
                          step = 0.01,
                          type='number',
                          min=0.01,
                          id={'type': 'k2-input', 'uid': uid}
                         ))
    ]))
    
    
    E0_input = dbc.Col(dbc.Row([
        dbc.Col([html.H5(['[E]',html.Sub('0'), ' mol/L'])]),
        dbc.Col(dbc.Input(value=1,
                          step = 0.1,
                          type='number',
                          min=0.1,
                          id={'type': 'E0-input', 'uid': uid}
                         ))
    ]))
    
    I_input = dbc.Col(dbc.Row([
        dbc.Col(dbc.Label('[I] mol/L')),
        dbc.Col(dbc.Input(value=0,
                          step = 0.1,
                          type='number',
                          min=0,
                          id={'type': 'I-input', 'uid': uid}
                         ))
    ]))
    
    
    KI_input = dbc.Col(dbc.Row([
        dbc.Col([html.H5(['K',html.Sub('I')])]),
        dbc.Col(dbc.Input(value=1,
                          step = 0.1,
                          type='number',
                          min=0,
                          id={'type': 'KI-input', 'uid': uid}
                         ))
    ]))
    
    I_type_dropdown = dbc.Col(dcc.Dropdown(id={'type': 'I-type-dropdown', 'uid':uid},
                                   options=[
                                       {'label': _('competitive'), 'value': 'competitive'},
                                        {'label': _('noncompetitive'), 'value': 'noncompetitive'},
                                        {'label': _('uncompetitive'), 'value': 'uncompetitive'}
                                   ],
                                   value='competitive'))


    clear_button = dbc.Button(_('Delete'), id={'type':'clear-button', 'uid':uid})    
    
    
    kinetics = dbc.Row([KM_input, k2_input, E0_input])
    inhibition = dbc.Row([I_input, KI_input, I_type_dropdown])
    
    controls_card = dbc.Card([kinetics, html.Hr(), inhibition, html.Hr(), clear_button ], body=True,
                             id={'type':'controls-card', 'uid':uid}, style={'margin-bottom':5})
    return controls_card


add_button = dbc.Button(_('Add plot'), id='add-button', style={'margin-bottom':5})


S_slider = dbc.Container([dbc.Label("[S] max = 0.5 mol/L", id='S-output'),
                          dcc.Slider(id = 'S-slider',
                                     min=0.1, max=5, step=0.1,
                                     marks={1: '1',
                                            2: '2',
                                            3: '3',
                                            4: '4',
                                            5: '5'},
                                     value=0.5)])

controls_container = dbc.Container([], id='controls-container', fluid=True)
plot_MM = dcc.Graph(id='plot-MM', style={'height': '60vh'}) # Michaelis-Menten
plot_LB = dcc.Graph(id='plot-LB', style={'height': '60vh'}) # Lineweaver-Burk
title = html.H1(_("Michaelis-Menten kinetics"), id='title')
subtitle = html.P(_("explore how changing parameters affects the kinetics"), id='subtitle')

left = dbc.Container([add_button, S_slider, html.Hr(), controls_container])
right = dbc.Row([dbc.Col(plot_MM), dbc.Col(plot_LB)])


# define the information widget. On clicking the info_button a short description of the model
# is shown
info_button = dbc.Button(id='info-button', n_clicks=0, children='More info')
# a text area that support mathjax and Latex for equations
info_text = dcc.Markdown('   ', mathjax=True, id='info-text')
# put button and text area togheter
info = dbc.Container([info_text, info_button])

title_col = dbc.Col(dbc.Container([title, subtitle]), width='auto')
info_col = dbc.Col(dbc.Container([info_text, info_button]), width='auto')
header = dbc.Row([title_col, info_col])

app.layout = dbc.Container([
    header,
    html.Hr(),
    dbc.Row([
        dbc.Col(left, xl=4,  align='right'),
        dbc.Col(right, xl=8, align='left')
        ])
    ],
    fluid=True
    )

   
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
        **Michaelis-Menten kinetics** is a kinetic mechanism describing simple enzyme catalized reactions in which a substrate, $\text{S}$, is converted in a product, $\text{P}$, in the presence of an enzyme, $\text{E}$.
        
        This mechanism was developed to explain the plot of the dependance of the initial rate, $v_0$, as a function of substrate concentration $[\text{S}]$ and can be can be schematized as
        
        $$\text{E} + \text{S} \overset{k_1}{\underset{k_{-1}}{\rightleftharpoons}} \text{ES} \overset{k_2}{\rightarrow} \text{E} + \text{P}$$
        
        In such mechanism $v_0$ will be
        
        $$v_0 = \frac{k_2[\text{E}]_0[\text{S}]}{K_M + [\text{S}]}$$
        
        where $[\text{E}]_0$ is the initial concentratin of the enzyme and $K_M$ is the **Michaelis constant**
        
        $$K_M = \frac{k_{-1}+k_2}{k_1}$$
        
        At high $[\text{S}]$ values the plot tends to a saturation value, the **limiting rate** $v_{max}$:
        
        $$v_{max}=k_2[\text{E}]_0$$
        
        In the presence of an **inhibitor**, $\text{I}$, the enzyme efficency can be reduced. There are different types of inhibitors with different mechanisms and kinetic effects.
        
        The analysis of kinetics inhibition is often conducted using the **Lineweaver-Burk plots** of $\frac{1}{v_0} vs. \frac{1}{[\text{S}]}$
        
        $$\frac{1}{v_0}=\frac{K_M}{v_{max}[\text{S}]}+\frac{1}{v_{max}}$$
        
        ''')
        button_text = _('less info')
    else:
        text = '   '
        button_text = _('more info')
    return button_text, text


@app.callback(Output('controls-container', 'children'),
              [Input('add-button', 'n_clicks'),
               Input({'type':'clear-button', 'uid': ALL}, 'n_clicks')],
              State('controls-container', 'children')
             )
def update_controls_container(add_n_clicks, clear_n_clicks, controls_container_list):
    '''update container adding or removing controls as required'''
    ctx = dash.callback_context # this is needed to know which button has been pushed
    trigger = ctx.triggered[0]
    if 'add-button' in trigger['prop_id']: # add a new panel
        uid = add_n_clicks # unique id 
        new_controls = controls_card_factory(uid=uid)
        return controls_container_list+[new_controls]
    else: # some delete button has been pushed
        match = re.search(r'"uid":(\d+)',trigger['prop_id'])
        if match:
            uid = int(match.group(1)) # uid of the card
            return [c for c in controls_container_list if c['props']['id']['uid'] != uid]
        else:
            raise PreventUpdate # needed when app starts         

@app.callback(Output({'type':'S-output', 'uid': MATCH}, 'children'),
              Input({'type':'S-slider', 'uid': MATCH}, 'value'))
def update_S_slider(val):
    return f"[S] max = {val} mol/L"
            
# this is the most important function
@app.callback([Output('plot-MM', 'figure'),
               Output('plot-LB', 'figure'),
               Output({'type':'controls-card', 'uid': ALL}, 'style')
              ],
              [Input('S-slider', 'value'),
               Input({'type':'KM-input', 'uid': ALL}, 'value'),
               Input({'type':'k2-input', 'uid': ALL}, 'value'),
               Input({'type':'E0-input', 'uid': ALL}, 'value'),
               Input({'type':'I-input', 'uid': ALL}, 'value'),
               Input({'type':'KI-input', 'uid': ALL}, 'value'),
               Input({'type':'I-type-dropdown', 'uid': ALL}, 'value')
              ],
              [State({'type':'controls-card', 'uid': ALL}, 'style')]
             )
def update_plots(Smax, KM_vals, k2_vals, E0_vals, I_vals, KI_vals, I_type_vals, styles):
    data_MM = []
    data_LB = []
    new_styles = []
    S = np.linspace(Smax*0, Smax, 1000)
    S[0] = S[0]+1e-8 # to avoid runtime error divide by zero
    if not KM_vals:
        raise PreventUpdate
    v0_inv_max = np.zeros(1)
    for i, (KM, k2, E0, I, KI, I_type, st) in enumerate(zip(KM_vals, k2_vals, E0_vals, I_vals, KI_vals, I_type_vals, styles)):
        if None in (KM, k2, E0, I, KI, I_type, st):
            raise PreventUpdate
        color = colors[i%len(colors)]
        st['border-color'] = color
        new_styles.append(st)
        v0, KM_eff, k2_eff = michaelis_menten(S, KM, k2, E0, I, KI, I_type)
        data_MM.append(go.Scatter(x=S, y=v0, mode='lines', line={'color': color}, showlegend=False))
        # compute extrapolation line for LB plots
        S_ex = [-1/KM_eff, 0] # this is actually 1/S
        v0_ex = [0, 1/(k2_eff*E0)] # this is actually 1/v0
        # avoid S == 0 first value
        data_LB.append(go.Scatter(x=1/S[1:], y=1/v0[1:], mode='lines', line={'color': color}, showlegend=False))
        data_LB.append(go.Scatter(x=S_ex, y=v0_ex, mode='lines', line={'color': color, 'dash': 'dash'}, showlegend=False))
        if (1/v0).max()>v0_inv_max.max():
            v0_inv_max = 1/v0
    layout_MM = {'xaxis': {'title': '[S]', 'range': (0, Smax)},
                 'yaxis': {'title': 'v\u2080', 'rangemode':'nonnegative'}}
    layout_LB = {'xaxis': {'title': '1/[S]', 'range': (-1/S[10], 1/S[10])},
                 'yaxis': {'title': '1/v\u2080', 'range':(0, v0_inv_max[10])}}
    plot_MM  = go.Figure(data=data_MM, layout=layout_MM)
    plot_LB = go.Figure(data=data_LB, layout=layout_LB)
    plot_LB.add_hline(y=0)
    plot_LB.add_vline(x=0)
    return plot_MM, plot_LB, new_styles

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
