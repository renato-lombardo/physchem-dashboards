import numpy as np
import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.colors as pcolors
import plotly.graph_objs as go
import re
from dash import callback, dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from flask import Flask, request
from flask_babel import Babel, gettext
try: # when running as an independent app
    from model import hill
except: # when running in a multipage dashboard
    from .model import hill
try: # when running as an independent app
    from utilities import _id, common_setup
except Exception as e: # when running in a multipage dashboard
    from .utilities import _id, common_setup
    

# define translator function
_ = gettext


#########################
# Dashboard information #
#########################
title = _("Hill equation")
subtitle = _("explore how changing parameters affects the saturation of hemoglobin")
info = _(r'''
        The **Hill-Langmuir equation** describes the interaction of a ligand, $L$, with a binding site. Specifically, it relates the **saturation**, $s$, to the ligand concentration.

        $$s = \frac{[L]^n}{([L]^n + K_d^n)}$$

        where $[L]$ is the molar concentration of the ligand, $K_d$ is the dissociation constant, and $n$ is the **Hill coefficient**, which describes the cooperativity of the binding process.

        The saturation corresponds to the ratio of occupied binding sites, $N_L$, to the total number of binding sites, $N$:

        $$ s = \frac{N_L}{N}
        ''')
order = 7

##################################
# common variables and utilities #
##################################

# colors for plotting different curves
colors = pcolors.qualitative.Plotly


#######################################
# set up general layout and callbacks #
#######################################
header, setup_language_general, show_info = common_setup(title, subtitle, info)

###########################
# dash element definition #
###########################

def controls_card_factory(uid=None):
    p50_slider = dbc.Container([html.H5(_('Bohr effect')),
                                dbc.Label(_("p50 = -- mbar"), id={'type':_id('p50-output'),'uid':uid}),
                                dcc.Slider(id = {'type':_id('p50-slider'), 'uid':uid},
                                           min=1, max=100, step=1,
                                           marks={20: '20 mbar',
                                                  40: '40 mbar',
                                                  60: '60 mbar',
                                                  80: '80 mbar',
                                                  100: '100 mbar'},
                                           value=35)])

    n_slider = dbc.Container([html.H5(_('Root effect')),
                              dbc.Label(_("n = --"), id={'type':_id('n-output'),'uid':uid}),
                              dcc.Slider(id = {'type':_id('n-slider'), 'uid':uid},
                                         min=0.1, max=10, step=0.1,
                                         marks={2: '2',
                                                4: '4',
                                                6: '6',
                                                8: '8',
                                                10: '10'},
                                         value=4)])

    clear_button = dbc.Button(_('Delete'), id={'type':_id('clear-button'), 'uid':uid})    
    
    
    controls_card = dbc.Card([p50_slider, html.Hr(), n_slider, html.Hr(), clear_button ], body=True,
                             id={'type':_id('controls-card'), 'uid':uid}, style={'margin-bottom':5})
    return controls_card

add_button = dbc.Button(_('Add plot'), id=_id('add-button'), style={'margin-bottom':5})
controls_container = dbc.Container([], id=_id('controls-container'), fluid=True)
plot = dcc.Graph(id=_id('plot'), style={'height': '80vh'})
pO2_slider = dbc.Container([html.H5("pO\u2082 --:-- mbar", id=_id('pO2-output')),
                            dcc.RangeSlider(id = _id('pO2-slider'),
                                            min=0, max=2000, step=50,
                                            marks={500: '500',
                                                   1000: '1000',
                                                   1500: '1500',
                                                   2000: '2000'},
                                            value=[0, 200])])

left = dbc.Container([add_button, pO2_slider, html.Hr(), controls_container])

def layout():
    layout = dbc.Container([
    header(),
    html.Hr(),
    dbc.Row([
        dbc.Col(left, align='left'),
        dbc.Col([plot], xl=8, align='left')
        ])
    ],
    fluid=True,
    id=_id('layout')
    )
    return layout


##########################
# set up specific layout #
##########################

@callback(Output(_id('controls-container'), 'children'),
              [Input(_id('add-button'), 'n_clicks'),
               Input({'type':_id('clear-button'), 'uid': ALL}, 'n_clicks')],
              State(_id('controls-container'), 'children')
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

@callback(Output({'type':_id('p50-output'), 'uid': MATCH}, 'children'),
              Input({'type':_id('p50-slider'), 'uid': MATCH}, 'value'))
def update_p50_slider(val):
    return f'p50 = {val} mbar'


@callback(Output({'type':_id('n-output'), 'uid': MATCH}, 'children'),
              Input({'type':_id('n-slider'), 'uid': MATCH}, 'value'))
def update_n_slider(val):
    return f'n = {val}'


@callback(Output(_id('pO2-output'), 'children'),
              Input(_id('pO2-slider'), 'value'))
def update_pO2_slider(val):
    return f'pO\u2082 = [{val[0]}-{val[1]}] mbar'

            
# this is the most important function
@callback([Output(_id('plot'), 'figure'),
               Output({'type':_id('controls-card'), 'uid': ALL}, 'style'),
              ],
              [Input({'type':_id('p50-slider'), 'uid': ALL}, 'value'),
               Input({'type':_id('n-slider'), 'uid': ALL}, 'value'),
               Input(_id('pO2-slider'), 'value')],
               [State({'type':_id('controls-card'), 'uid': ALL}, 'style')]
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

@callback([Output(_id('add-button'), 'children')],
          [Input(_id('add-button'), 'children')])
def setup_language(*messages):
    return [_(m) for m in messages]


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
    translation = __name__.rsplit('.',1)[0].replace('.', '/') + '/translations'
    dash.register_page(
        __name__,
        title=title,
        name=title,
        subtitle=subtitle,
        info=info,
        order=order,
        translation=translation
)