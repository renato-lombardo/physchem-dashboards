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
from model import hill

# define translator function
_ = gettext

colors = px.colors.qualitative.Plotly

####################
# Initilialize app #
####################
# create the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# use language that best matches the browser

# utility function for locale selection
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())

# intialize Flask-babel
babel = Babel(app.server) # app.server is the Flask app inside the dash app.
with app.server.app_context():
    LANGUAGES = {l.language: l.get_language_name() for l in babel.list_translations()}
    babel.init_app(app.server, locale_selector=get_locale)
app.config.update({'title': _('Hill equation')})

###########################
# dash element definition #
###########################

def controls_card_factory(uid=None):
    p50_slider = dbc.Container([html.H5(_('Bohr effect')),
                                dbc.Label(_("p50 = -- mbar"), id={'type':'p50-output','uid':uid}),
                                dcc.Slider(id = {'type':'p50-slider', 'uid':uid},
                                           min=1, max=100, step=1,
                                           marks={20: '20 mbar',
                                                  40: '40 mbar',
                                                  60: '60 mbar',
                                                  80: '80 mbar',
                                                  100: '100 mbar'},
                                           value=35)])

    n_slider = dbc.Container([html.H5(_('Root effect')),
                              dbc.Label(_("n = --"), id={'type':'n-output','uid':uid}),
                              dcc.Slider(id = {'type':'n-slider', 'uid':uid},
                                         min=0.1, max=10, step=0.1,
                                         marks={2: '2',
                                                4: '4',
                                                6: '6',
                                                8: '8',
                                                10: '10'},
                                         value=4)])

    clear_button = dbc.Button(_('Delete'), id={'type':'clear-button', 'uid':uid})    
    
    
    controls_card = dbc.Card([p50_slider, html.Hr(), n_slider, html.Hr(), clear_button ], body=True,
                             id={'type':'controls-card', 'uid':uid}, style={'margin-bottom':5})
    return controls_card

add_button = dbc.Button(_('Add plot'), id='add-button', style={'margin-bottom':5})
controls_container = dbc.Container([], id='controls-container', fluid=True)
plot = dcc.Graph(id='plot', style={'height': '80vh'})
title = html.H1(_("Hill equation"), id='title')
subtitle = html.P(_("explore how changing parameters affects the saturation of hemoglobin"), id='subtitle')
pO2_slider = dbc.Container([html.H5("pO\u2082 --:-- mbar", id='pO2-output'),
                            dcc.RangeSlider(id = 'pO2-slider',
                                            min=0, max=2000, step=50,
                                            marks={500: '500',
                                                   1000: '1000',
                                                   1500: '1500',
                                                   2000: '2000'},
                                            value=[0, 200])])

left = dbc.Container([add_button, pO2_slider, html.Hr(), controls_container])

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
        dbc.Col(left, align='left'),
        dbc.Col([plot], xl=8, align='left')
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
        The **Hill-Langmuir equation** describes the interaction of a ligand, $L$, with a binding site. Specifically, it relates the **saturation**, $s$, to the ligand concentration.

        $$s = \frac{[L]^n}{([L]^n + K_d^n)}$$

        where $[L]$ is the molar concentration of the ligand, $K_d$ is the dissociation constant, and $n$ is the **Hill coefficient**, which describes the cooperativity of the binding process.

        The saturation corresponds to the ratio of occupied binding sites, $N_L$, to the total number of binding sites, $N$:

        $$ s = \frac{N_L}{N}
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

@app.callback(Output({'type':'p50-output', 'uid': MATCH}, 'children'),
              Input({'type':'p50-slider', 'uid': MATCH}, 'value'))
def update_p50_slider(val):
    return f'p50 = {val} mbar'


@app.callback(Output({'type':'n-output', 'uid': MATCH}, 'children'),
              Input({'type':'n-slider', 'uid': MATCH}, 'value'))
def update_n_slider(val):
    return f'n = {val}'


@app.callback(Output('pO2-output', 'children'),
              Input('pO2-slider', 'value'))
def update_pO2_slider(val):
    return f'pO\u2082 = [{val[0]}-{val[1]}] mbar'

            
# this is the most important function
@app.callback([Output('plot', 'figure'),
               Output({'type':'controls-card', 'uid': ALL}, 'style'),
              ],
              [Input({'type':'p50-slider', 'uid': ALL}, 'value'),
               Input({'type':'n-slider', 'uid': ALL}, 'value'),
               Input('pO2-slider', 'value')],
               [State({'type':'controls-card', 'uid': ALL}, 'style')]
             )
def update_plot(p50_list, n_list, pO2, styles):
    data = []
    new_styles = []
    for i, (p50, n, st) in enumerate(zip(p50_list, n_list, styles)):
        color = colors[i%len(colors)]
        st['border-color'] = color
        new_styles.append(st)
        pvals = np.linspace(pO2[0], pO2[1], 1000)
        s = hill(pvals, p50, n)
        data.append(go.Scatter(x=pvals, y=s, mode='lines', line={'color': color}, showlegend=True,
                    name=f'p50 = {p50}, n = {n}'))
    layout = {'xaxis': {'title': 'pO\u2082 /mbar', 'range': (pO2[0], pO2[1])},
              'yaxis': {'title': _('saturation'), 'range': (0, 1)}}
    return go.Figure(data=data, layout=layout), new_styles

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
    app.run_server(debug=True, host='0.0.0.0', port=5000)
