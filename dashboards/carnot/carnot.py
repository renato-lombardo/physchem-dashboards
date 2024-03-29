import numpy as np
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import callback, dash_table, dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from dash.dash_table.Format import Format, Scheme
from flask import Flask, request
from flask_babel import Babel, gettext
try: # when running as an independent app
    from model import carnot
except: # when running in a multipage dashboard
    from .model import carnot
try: # when running as an independent app
    from utilities import _id, common_setup
except: # when running in a multipage dashboard
    from .utilities import _id, common_setup
    

# define translator function
_ = gettext

#########################
# Dashboard information #
#########################
title = _("Carnot cycle")
subtitle = _("explore how the thermodynamics parameters change on changing the volumes and/or temperatures")
info = _(r'''
        **Carnot cycle** describes the thermodynamical behavior of the **Carnot engine**.
        It consists of four steps, each performed in a reversible way.
        
        The total change of each state function ($U$, $S$, $p$, $V$, $T$)  during a cycle is zero, being the initial and final point coincident. However, the amounts of work and heat (that are path functions) are not zero.
        
        The total amount of work, $w$, corresponds to the difference bewteen the heat absorbed from the hot reservoir, $q_H$, and the heat trasferred to the cold reservoir, $q_C$:
        
        $$w = q_H - q_C$$
        
        The efficiency of any engine, $\eta$, is defined as:
        
        $$\eta = \frac{w}{q_H} = \frac{q_H - q_C}{q_H}$$
        
        For a Carnot engine it is possible to derive that $\eta$ is also:
        
        $$\eta = \frac{T_H - T_C}{T_H} = 1 - \frac{T_C}{T_H}$$
        
        ''')
order = 6

##################################
# common variables and utilities #
##################################

def update_table(row_names, columns, row_data):
    data = []
    for i, r in enumerate(row_names):
        row = {'row_name': r}
        for c in columns:
            row[c] = row_data[i][c]
        data.append(row)
    return data


#######################################
# set up general layout and callbacks #
#######################################
header, setup_language_general, show_info = common_setup(title, subtitle, info)

##########################
# set up specific layout #
##########################

T_range = (5, 1000)
V_range = (0.1, 10)

Tc_input = dbc.Container([dbc.Label(_('T cold /K'), id=_id('Tc-label')),
                          dbc.Input(id=_id('Tc-input'), type='number',
                                    min=T_range[0], max=T_range[1], step=1, value=250)],
                        fluid=True)
Th_input = dbc.Container([dbc.Label(_('T hot /K'), id=_id('Th-label')),
                          dbc.Input(id=_id('Th-input'), type='number',
                                    min=T_range[0], max=T_range[1], step=1, value=300)],
                        fluid=True)
V1_input = dbc.Container([dbc.Label(_('V\u2081 /\u33A5'), id=_id('V1-label')),
                          dbc.Input(id=_id('V1-input'), type='number',
                                    min=V_range[0], max=V_range[1], step=0.1, value=1.0)],
                        fluid=True)
V2_input = dbc.Container([dbc.Label(_('V\u2082 /\u33A5'), id=_id('V2-label')),
                          dbc.Input(id=_id('V2-input'), type='number',
                                    min=V_range[0], max=V_range[1], step=0.1, value=2.0)],
                        fluid=True)

control_panel = dbc.Container([dbc.Row([dbc.Col(Tc_input), dbc.Col(Th_input)]),
                               html.P(),
                               dbc.Row([dbc.Col(V1_input), dbc.Col(V2_input)])])
control_panel = dbc.Container([dbc.Row([dbc.Col(Tc_input), dbc.Col(Th_input), dbc.Col(V1_input), dbc.Col(V2_input)])], fluid=True)


eta_output = html.H3(_('\u03B7 = --'), id=_id('eta-output'))
w_tot_output = html.H3(_('w = --'), id=_id('w-tot-output'))

out_panel = dbc.Row([dbc.Col(eta_output), dbc.Col(w_tot_output)])

plot = dcc.Graph(id=_id('PV-plot'), style={'height':'70vh'})

# states
s_table = dash_table.DataTable(id = _id('s-table'),
                columns = [
                        {'name': '', 'id': _id('row_name'), 'type': 'text'},
                        {'name': _('V /\u33A5'), 'id': _id('V'), 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)},
                        {'name': _('p /Pa'), 'id': _id('p'), 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)},
                        {'name': _('T /K'), 'id': _id('T'), 'type': 'numeric', 'format': Format(precision=1, scheme=Scheme.fixed)}
                        ],
                    data = [],
                    editable = False,
                    export_format='csv',
                    page_action='none',
                    style_table={'height': '300px', 'overflowY': 'auto'})


# trajectories 
t_table = dash_table.DataTable(id = _id('t-table'),
                columns = [
                        {'name': '', 'id': _id('row_name'), 'type': 'text'},
                        {'name': _('w /J'), 'id': _id('w'), 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)},
                        {'name': _('q /J'), 'id': _id('q'), 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)},
                        {'name': _('\u2206U /J'), 'id': _id('DU'), 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)},
                        {'name': _('\u2206S /J'), 'id': _id('DS'), 'type': 'numeric', 'format': Format(precision=3, scheme=Scheme.fixed)}
                        ],
                    data = [],
                    editable = False,
                    export_format='csv',
                    page_action='none',
                    style_table={'height': '300px', 'overflowY': 'auto'})


left = dbc.Container([out_panel, html.Hr(), s_table, t_table], fluid=True)
right = dbc.Container([control_panel, plot], fluid=True)

def layout():
    layout = dbc.Container([header(),
                            html.Hr(),
                            dbc.Row([dbc.Col(left, xl=4),
                                     dbc.Col(right, xl=6)
                                    ])],
                           fluid=True,
                           id=_id('layout')
                           )
    return layout


#############
# Callbacks #
#############

# this is the most important function
@callback([
               Output(_id('PV-plot'), 'figure'),
               Output(_id('t-table'), 'data'),
               Output(_id('s-table'), 'data'),
               Output(_id('eta-output'), 'children'),
               Output(_id('w-tot-output'), 'children'),
              ],
              [
               Input(_id('Tc-input'), 'value'),  
               Input(_id('Th-input'), 'value'),  
               Input(_id('V1-input'), 'value'),  
               Input(_id('V2-input'), 'value'),  
              ]
             )
def update_plot_table(Tc, Th, V1, V2):
    if None in (Tc, Th, V1, V2): # values outside ranges 
        return go.Figure(), [], [], '--', '--'
    for val, vrange in zip((Tc, Th, V1, V2), (T_range, T_range, V_range, V_range)):
        if (val<vrange[0]) or (val>vrange[1]):
            return go.Figure(), [], [],  '--', '--'
    if V1>=V2:
        return go.Figure(), [], [], '--', '--'
    
    s, t, eta, w_tot = carnot(Tc, Th, V1, V2)
    sV = [s[i]['V'] for i in range(len(s))]
    sp = [s[i]['p'] for i in range(len(s))]
    names = [_('Isothermal expansion'), _('Adiabatic expansion'), _('Isothermal compression'), _('Adiabatic compression')]
    data = [go.Scatter(x=t[i]['V'], y=t[i]['p'], name=names[i]) for i in range(len(t))]
    data.append(go.Scatter(x=sV, y=sp, mode='markers+text', text=['1', '2', '3', '4'],
                           marker=dict(size=15, color='white', line=dict(color='black', width=1) ),
                           showlegend=False))
    fig = go.Figure(data=data)
    fig.update_layout(xaxis_title=_('V/ \u33A5'), yaxis_title=_('p /Pa'))
    columns = ['w', 'q', 'DU', 'DS']
    t_data = update_table(names, columns, t)
    columns = ['V', 'p', 'T']
    sn = _('state')
    state_names = [f'{sn} {i}' for i in range(1,5)]
    s_data = update_table(state_names, columns, s)
    return fig, t_data, s_data, f'\u03B7 = {eta:.3f}', f'w = {w_tot:,.3f} J'

@callback([
               Output(_id('Tc-label'), 'children'),
               Output(_id('Th-label'), 'children'),
               Output(_id('V1-label'), 'children'),
               Output(_id('V2-label'), 'children'),
              ],
              [
               Input(_id('Tc-label'), 'children'),
               Input(_id('Th-label'), 'children'),
               Input(_id('V1-label'), 'children'),
               Input(_id('V2-label'), 'children'),
              ])
def setup_language_specific(*messages):
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