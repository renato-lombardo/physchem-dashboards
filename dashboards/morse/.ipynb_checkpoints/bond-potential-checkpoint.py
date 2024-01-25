import numpy as np
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import pint
import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
import re
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from flask import Flask, request
from flask_babel import Babel, gettext
from model import oscillator, molecules

# define translator function
_ = gettext

#########################
# Dashboard information #
#########################
title = 'Bond potential'
subtitle = 'explore how each curve changes on changing the parameters'
info = r'''
        **Hooke potential** (elastic potential energy) can be used as a simple model for the chemical bond. Its expression is:  
        
        $$V = \frac{1}{2} k (r-r_e)^2$$  
        
        In this model the bond never breaks. It is a suitable model when the energy are not very large.  
        
        **Morse potential** (anelastic potential energy) is a more complex model for the chemical bond. Its expression is:  
        
        $$V = D_e \left( \left[1-e^{-\alpha(r-r_e)} \right)^2 -1 \right]$$  
        
        In this model there is a **dissociation limit**, an energy at which the bond breaks. $D_e$ is the **potential well**, the deeper the well, the higher the bond energy (i.e. the work needed to break the bond).
        '''
order = 2

##################################
# common variables and utilities #
##################################
# initialize units registry
ureg = pint.UnitRegistry()
# import colors list for plotly plots
colors = px.colors.qualitative.Plotly
# generate labels for each molecule to use in the dashboard
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


##########################
# set up specific layout #
##########################

def controls_card_factory(uid=None):
    '''generate a card with all the controls for each curve'''
    
    molecule_dropdown = dcc.Dropdown(id={'type':'molecule-dropdown', 'uid': uid},
                                     options=[{"label": molecules[m]['label'], "value": m} for m in molecules.keys()],
                                     value='Br_2')
    

    h_container = dbc.Container([dbc.Row([
                                 dbc.Col(daq.BooleanSwitch(id={'type':'h-plot-switch', 'uid':uid},
                                                           on=False,
                                                           label='Hooke',
                                                           labelPosition='left')),
                                 dbc.Col(daq.BooleanSwitch(id={'type':'h-levels-switch', 'uid':uid},
                                                           on=False,
                                                           label=_('Levels'),
                                                           labelPosition='left'))])
                                ]) 
    m_container = dbc.Container([dbc.Row([
                                 dbc.Col(daq.BooleanSwitch(id={'type':'m-plot-switch', 'uid':uid},
                                                           on=True,
                                                           label='Morse',
                                                           labelPosition='left')),
                                 dbc.Col(daq.BooleanSwitch(id={'type':'m-levels-switch', 'uid':uid},
                                                           on=False,
                                                           label=_('Levels'),
                                                           labelPosition='left'))])
                                ])
    
    clear_button = dbc.Button(_('Delete'), id={'type':'clear-button', 'uid':uid})
    
    controls_card = dbc.Card([dbc.Row([dbc.Col(molecule_dropdown), dbc.Col(clear_button)]),
                              dbc.Row([dbc.Col(m_container)]),
                              dbc.Row([dbc.Col(h_container)])],
                             body=True, id={'type':'controls_card', 'uid':uid}, style={'margin-bottom':5})
    return controls_card

r_slider = dbc.Container([dbc.Label(_('distance'), id='distance-label'),
                          dcc.Slider(id = 'r-slider',
                                     min=1, max=10, step=10,
                                     marks={2: '2 \u212B',
                                            4: '4 \u212B',
                                            6: '6 \u212B',
                                            8: '8 \u212B',
                                            10: '10 \u212B'},
                                     value=6)])

curves_container = dbc.Container([], id='curves-container') # put all the cards together
add_button = dbc.Button(_('add plot'), id='add-button', style={'margin-bottom':5})
left_panel = dbc.Container([r_slider, add_button, curves_container], id='left-panel')
def layout():
    'set layout of the app with all the widgets'
    layout = dbc.Container([
        header(),
        html.Hr(),
        dbc.Row([dbc.Col(left_panel, xl=3),
                 dbc.Col(dcc.Graph(id="V-plot", style={'height':'80vh'}), xl=7),],
                 align="center",),],                           
        fluid=True,
        id='layout'
        )
   

######################
# specific callbacks #
######################
@app.callback([Output('distance-label', 'children'),
               Output('add-button', 'children'),
              ],
              [Input('distance-label', 'children'),
               Input('add-button', 'children'),
              ])
def setup_language_specific(*messages):
    return [_(m) for m in messages]
    
@app.callback(Output('curves-container', 'children'),
              [Input('add-button', 'n_clicks'),
              Input({'type':'clear-button', 'uid': ALL}, 'n_clicks')],
              State('curves-container', 'children'),
        )
def update_curves_container(add_n_clicks, clear_n_clicks, curves_container_list):
    '''update curves-container adding or removing controls as required'''
    ctx = dash.callback_context # this is needed to know which button has been pushed
    trigger = ctx.triggered[0]
    if 'add-button' in trigger['prop_id']: # add a new controls_card
        uid = add_n_clicks # unique id 
        new_controls_card = controls_card_factory(uid=uid)
        return curves_container_list+[new_controls_card]
    else: # some delete button has been pushed
        match = re.search(r'"uid":(\d+)',trigger['prop_id'])
        if match:
            uid = int(match.group(1)) # uid of the curve
            new_list = [curve for curve in curves_container_list
                        if curve['props']['id']['uid'] != uid]
            return new_list
        else:
            raise PreventUpdate # needed when app starts

            
# This is the most important callback doing nearly all the work
@app.callback([Output('V-plot', 'figure'),
               Output('V-plot', 'config'),
               Output({'type':'controls_card', 'uid': ALL}, 'style'),
              ],
              [Input('r-slider', 'value'),
               Input({'type':'molecule-dropdown', 'uid': ALL}, 'value'),
               Input({'type':'m-plot-switch', 'uid': ALL}, 'on'),
               Input({'type':'m-levels-switch', 'uid': ALL}, 'on'),
               Input({'type':'h-plot-switch', 'uid': ALL}, 'on'),
               Input({'type':'h-levels-switch', 'uid': ALL}, 'on'),
              ],
              State({'type':'controls_card', 'uid': ALL}, 'style'),
)
def update_plot(r_max, mols, morse, morse_levels, hooke, hooke_levels, style):
    '''update plots area values on panel everytime something changes'''
    data = []
    new_style = []
    Dmax = 0
    xmin = r_max
    r = np.linspace(0, r_max, 1000)
    n_lines = 30
    for i, (mol, m_plot, ml_plot, h_plot, hl_plot, st) in enumerate(zip(mols, morse, morse_levels, hooke, hooke_levels, style)):
        color = colors[i%len(colors)]
        mym = oscillator(mol, 'morse', r=r)
        myh = oscillator(mol, 'hooke', r=r, nu_max=mym.nu_max, De=mym.De)
        if h_plot: # Hooke potential without levels
            x = myh.r.to('angstrom').magnitude
            y = myh.V.to('eV').magnitude
            data.append(go.Scatter(x=x, y=y, mode='lines', name=f'{molecules[mol]["label2"]} - Hooke', line={'color':color, 'width':2}, opacity=0.5, showlegend=True))
        if hl_plot: # Hooke potential with energy levels
            step =int(len(myh.lines)/n_lines) or 1
            for l in myh.lines[::step]:
                lx = l[0].to('angstrom').magnitude
                ly = l[1].to('eV').magnitude
                data.append(go.Scatter(x=lx, y=ly, mode='lines', line={'color':color, 'width':0.5}, opacity=0.5, showlegend=False))
        if m_plot: # Morse potential without energy levels
            x = mym.r.to('angstrom').magnitude
            y = mym.V.to('eV').magnitude
            data.append(go.Scatter(x=x, y=y, mode='lines', name=f'{molecules[mol]["label2"]} - Morse', line={'color':color, 'width':2}, showlegend=True))
        if ml_plot: # Morse potential with energy levels
            step =int(len(mym.lines)/n_lines) or 1
            for l in mym.lines[::step]:
                lx = l[0].to('angstrom').magnitude
                ly = l[1].to('eV').magnitude
                data.append(go.Scatter(x=lx, y=ly, mode='lines', line={'color':color, 'width':0.5}, showlegend=False))
        # update border color 
        st['border-color'] = color
        new_style.append(st)
        Dmax = max((Dmax, mym.De.to('eV').magnitude))
        xmin = min(xmin, myh.lines[-1][0].to('angstrom').magnitude[0])
    layout = {'xaxis': {'title': _('distance, \u212B'), 'range':[xmin, r_max]},
              'yaxis': {'title': _('energy, eV') , 'range':[-1.2*Dmax, 0.5*Dmax]}}
    layout.update(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1)
    )
    myfig = go.Figure(data=data, layout=layout)
    myfig.add_hline(y=0, line_dash="dash")
    config = {'locale':get_locale()}
    return myfig, config, new_style, 

if __name__ == '__main__':
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
    app.layout = layout()
    app.run_server(debug=True, host='0.0.0.0', port=5000)
else: # use as a page in a dash multipage app
    dash.register_page(
        __name__,
        path=__name__,
        title=title,
        name=title,
        subtitle=subtitle,
        info=info,
        order=order
)
    app.run_server(debug=True, host='0.0.0.0', port=5000)
