import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
import re
from dash import callback, dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from flask import Flask, request
from flask_babel import Babel, gettext
from model import MB, v_p, v_avg, v_rms, molecules

# define translator function to use with flask_babel
_ = gettext

#########################
# Dashboard information #
#########################
title = html.H1(_("Maxwell-Boltzmann distribution"), id='title')
subtitle = html.P(_('explore how each curve changes on changing the parameters'), id='subtitle')
info = _(r'''
        The probability $P$ that a molecule has a speed between $v$ and $v + \Delta v$ is  
        $$P = \int_v^{v + \Delta v} F(v) dv$$  
        $F(v)$ is the **probability density**  that depends on speed $v$, mass of the molecule, $m$ and temperature, $T$ according to Maxwell Boltzmann equation  
        $F(v) = \sqrt { \left( \frac{m}{2 \pi k T} \right)^3  }4 \pi v^2 e^{-\frac{mv^2}{2kT}}$
        ''')

##################################
# common variables and utilities #
##################################

# colors for plotting different curves
colors = px.colors.qualitative.Plotly

# dictionary with all the characterstics speed information
# func: funtion used to compute v, label: for dropdown menu, dash: type of dash for plot
v_dict = {'v_p': {'func': v_p, 'label': html.Span(['v', html.Sub('p')]), 'dash': 'dash'},
  'v_avg': {'func': v_avg, 'label': html.Span(['v', html.Sub('avg')]), 'dash': 'dot'},
  'v_rms': {'func': v_rms, 'label': html.Span(['v', html.Sub('rms')]), 'dash': 'dashdot'}}

# labels for each molecule to use in the dashboard
# label: for the dropdown widget, label2: for the plot legend
for mol in molecules:
    if '_' in mol:
        symbol, num = mol.split('_')
        molecules[mol]['label'] = html.Span([symbol, html.Sub(num)])
        molecules[mol]['label2'] = f'{symbol}<sub>{num}</sub>'
    else:
        symbol = mol
        molecules[mol]['label'] = html.Span([symbol])
        molecules[mol]['label2'] = f'{symbol}'


#######################################
# set up general layout and callbacks #
#######################################

# define the information widget. On clicking the info_button a short description of the model
# is shown
info_button = dbc.Button(id='info-button', n_clicks=0, children='More info')
# a text area that support mathjax and Latex for equations
info_text = dcc.Markdown('   ', mathjax=True, id='info-text')
# put button and text area togheter
title_col = dbc.Col(dbc.Container([title, subtitle]), width='auto')
info_col = dbc.Col(dbc.Container([info_text, info_button]), width='auto')
header = dbc.Row([title_col, info_col])

@callback([Output('info-button', 'children'),
               Output('info-text', 'children')],
              Input('info-button', 'n_clicks')
             )
def show_info(n_clicks):
    '''show a short information about the model '''
    if n_clicks%2: # button pressed for an uneven number of times
        text = info
        button_text = _('less info') # change the label
    else: # clicked again after showing, means hide the info
        text = '   '
        button_text = _('more info')
    return button_text, text


##########################
# set up specific layout #
##########################

def controls_card_factory(uid=None):
    '''generate a card with all the controls for each curve added'''
    
    molecule_dropdown = dcc.Dropdown(id={'type':'molecule-dropdown', 'uid': uid},
                                     options=[{'label': molecules[m]['label'], 'value': m} for m in molecules],
                                     value='O_2')

    temperature_slider = dbc.Container([dbc.Label(_("temperature not set"), id={'type':'temperature-output','uid':uid}),
                                    dcc.Slider(id = {'type':'temperature-slider', 'uid':uid},
                                               min=200, max=1000, step=10,
                                               tooltip={"placement": "bottom", "always_visible": False},
                                               marks={200: '200 K',
                                                      400: '400 K',
                                                      600: '600 K',
                                                      800: '800 K',
                                                      1000: '1000 K'},
                                               value=300)])
    
    speed_checklist = dbc.Checklist(options=[{'label': v_value['label'], 'value': v_key} for v_key, v_value in v_dict.items()],
                                   value=[], id={'type':'speed-checklist', 'uid':uid})
    

    area_slider = dbc.Container([daq.BooleanSwitch(id={'type':'area-switch', 'uid':uid},
                                                   on=False,
                                                   label=_('Probability'),
                                                   labelPosition='left'),
                                dcc.RangeSlider(id = {'type':'area-slider', 'uid':uid},
                                           min=0, max=6000, step=50,
                                           tooltip={"placement": "bottom", "always_visible": False},
                                           marks={0: '0 m/s',
                                                  2000: '2000 m/s',
                                                  4000: '4000 m/s',
                                                  6000: '6000 m/s'},
                                           value=[0, 6000], disabled=True)
                            ],)
    clear_button = dbc.Button(_('Delete'), id={'type':'clear-button', 'uid':uid})    
    
    # assemble the card
    controls_card = dbc.Card([ # a card
        #a row with multiple columns
        dbc.Row([dbc.Col(dbc.Row([dbc.Col(molecule_dropdown),
                 dbc.Col(clear_button)])),
                 dbc.Col(speed_checklist)
        ]),
        temperature_slider,
        area_slider
    ], body=True, id={'type':'controls_card', 'uid':uid}, style={'margin-bottom':5})
    return controls_card

# put all the cards together
curves_container = dbc.Container([], id='curves-container')
# button to add a new plot
add_button = dbc.Button(_('Add plot'), id='add-button', style={'margin-bottom':5})
#left panel containing all the plots and the button
left_panel = dbc.Container([add_button, curves_container], id='left-panel')

# specific layout of the app with all the widgets
layout = dbc.Container([
    header,
    html.Hr(),
    dbc.Row([dbc.Col(left_panel, xl=3),
        dbc.Col(dcc.Graph(id="MB-plot", style={'height':'80vh'}), xl=7),],
             align="center",),
],
fluid=True,
)

######################
# specific callbacks #
######################

@callback([Output('add-button', 'children'),
               Output('title', 'children'),
               Output('subtitle', 'children'),
              ],
              [Input('add-button', 'children'),
               Input('title', 'children'),
               Input('subtitle', 'children'),
              ])
def setup_language(*messages):
    return [_(m) for m in messages]
    
@callback(Output('curves-container', 'children'),
              [Input('add-button', 'n_clicks'),
              Input({'type':'clear-button', 'uid': ALL}, 'n_clicks')],
              State('curves-container', 'children'),
        )
def update_curves_container(add_n_clicks, clear_n_clicks, curves_container_list):
    '''update curves-container adding or removing controls as required'''
    ctx = dash.callback_context # this is needed to know which button has been pushed
    trigger = ctx.triggered[0]
    if 'add-button' in trigger['prop_id']: # add a new controls_card
        uid = add_n_clicks # generate a unique id for each curve
        new_controls_card = controls_card_factory(uid=uid)
        return curves_container_list+[new_controls_card]
    else: # some delete button has been pushed
        # find witch uid
        match = re.search(r'"uid":(\d+)',trigger['prop_id'])
        if match:
            uid = int(match.group(1)) # uid of the curve
            #regenerate the list of curves, removing uid
            new_list = [curve for curve in curves_container_list
                        if curve['props']['id']['uid'] != uid]
            return new_list
        else:
            raise PreventUpdate # needed when app starts for the first time
        
@callback(Output({'type':'temperature-output', 'uid': MATCH}, 'children'),
              Input({'type':'temperature-slider', 'uid': MATCH}, 'value'))
def display_temperature_value(value):
    return _('temperature') + f' {value} K'


@callback(Output({'type':'area-slider', 'uid': MATCH}, 'disabled'),
              Input({'type':'area-switch', 'uid': MATCH}, 'on'))
def activate_area_slider(on):
    return not on

# This is the most important callback doing nearly all the work
@callback([Output("MB-plot", "figure"),
               Output({'type':'controls_card', 'uid': ALL}, 'style'),
               Output({'type':'area-switch', 'uid': ALL}, 'label'),
               Output({'type':'speed-checklist', 'uid': ALL}, 'options')
              ],
              [Input({'type':'molecule-dropdown', 'uid': ALL}, 'value'),
               Input({'type':'temperature-slider', 'uid': ALL}, 'value'),
               Input({'type':'area-switch', 'uid': ALL}, 'on'),
               Input({'type':'area-slider', 'uid': ALL}, 'value'),
               Input({'type':'speed-checklist', 'uid': ALL}, 'value')
              ],
              State({'type':'controls_card', 'uid': ALL}, 'style'),
              State({'type':'speed-checklist', 'uid': ALL}, 'options')
)
def update_plot(mols, T_vals, a_switch, v_range, v_selected, style, options):
    '''update plots and values on the relative panel everytime something changes'''
    data = []
    v = np.linspace(0, 6000, 1000)
    new_style = []
    new_label = []
    new_options = [] 
    for i, (mol, T, a_s, v_r, v_s, st, opt) in enumerate(zip(mols, T_vals, a_switch, v_range, v_selected, style, options)):
        if not mol:
            break
        # find the molecular mass for the chosen molecule in the dictionary
        M = molecules[mol]['M']
        # compute the probability density
        fv = MB(v, M, T)
        show=True
        label = _('Probability ---')
        # choose the correct color
        color = colors[i%len(colors)]
        mol_label = molecules[mol]['label2'] + f' - {T} K'
        if a_s and v_r: # plot area requested
            idx = v.searchsorted(v_r)
            v2 = v[idx[0]:idx[1]]
            # compute probability density in the speed range v2
            fv2 = MB(v[idx[0]:idx[1]], M, T)
            #append the plot to data, filling the area below the curve
            data.append(go.Scatter(x=v2, y=fv2, mode='lines', fill='tozeroy', name=mol_label, line={'color':color}, showlegend=True))
            show=False
            # compute the integral, e.g. the probability
            prob = np.trapz(fv2, dx=v2[1]-v2[0])
            # update the probability value in the controls card
            label = _('Probability') + f'[{v_r[0]}-{v_r[1]}] m/s = {prob:.3f}'
        # plot the distribution curve
        data.append(go.Scatter(x=v, y=fv, mode='lines', name=mol_label, line={'color':color}, showlegend=show))
        # update border color for the specific controls card 
        st['border-color'] = color
        new_style.append(st)
        # update characteristic speeds values
        opt2 = []
        for o in opt:
            v_type = o['value']
            v_val = v_dict[v_type]['func'](M, T)
            v_label = html.Span(list(v_dict[v_type]["label"].children)) # use list() to make a copy of the original list
            v_unit = html.Span(['m', html.Sup('-1')]) # trick because you cannot put a \ sign into a f-string directly
            #v_label.children = v_label.children[0:2] # take just the name
            v_label.children.append(f' = {v_val:.0f}') # append value
            v_label.children.append(html.Span([' m s', html.Sup('-1')])) # append units
            opt2.append({'label': v_label,
                         'value': v_type
                        })
            if v_type in v_s: # plot speed value has been selected
                dash = v_dict[v_type]['dash']
                data.append(go.Scatter(x=[v_val, v_val], y=[0, MB(v_val, M, T)],
                                       mode='lines', showlegend=False,
                                       line={'dash':dash, 'color':color}))
        new_options.append(opt2)
        # update probability         
        new_label.append(label)
    layout = {'xaxis': {'title': _('speed m/s')}, 'yaxis': {'title': _('probability density s/m')}, 'legend':{'orientation': 'h'}}
    layout.update(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1)
        )
    return go.Figure(data=data, layout=layout), new_style, new_label, new_options

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
        order=1
)