import numpy as np
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import callback, dcc, html
from dash.dependencies import Input, Output, State
from flask import Flask, request
from flask_babel import Babel, gettext
from plotly.subplots import make_subplots
try: # when running as an independent app
    from model import Ehrenfest
except: # when running in a multipage dashboard
    from .model import Ehrenfest
try: # when running as an independent app
    from utilities import _id, common_setup
except Exception as e: # when running in a multipage dashboard
    from .utilities import _id, common_setup
    

# define translator function
_ = gettext

#########################
# Dashboard information #
#########################
title = _('Ehrenfest model')
subtitle = _('observe gas expansion')
info = _(r'''
    The **Ehrenfest model** is a simple representation of what happens during the expansion of a perfect gas. In this applet you can choose how many particles to put initially in box A and box B and how many steps of the model to simulate. After that, you can create the simulation by clicking on **generate** and observe what happens clicking on **play**. The plot  on the right top shows the fraction of particles, $f$, in the boxes ad each instant:  
    $$f_A = \frac{N_A}{N}$$
    while the plot a the right bottom shows the probability distribution of a **fluctuation**, at each instant. The fluctuation is the difference of population between the boxes divided by the total number of particles in the system:  
    
    $$fluct = \frac{N_A- N_B}{N}$$
    
    ''')
order = 5

#######################################
# set up general layout and callbacks #
#######################################
header, setup_language_general, show_info = common_setup(title, subtitle, info)
"""
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
"""

##########################
# set up specific layout #
##########################

steps_input = dbc.Row([dbc.Col(dbc.Label(_('steps'), id=_id('steps-label')), md=2),
                       dbc.Col(dbc.Input(id = _id('steps-input'), type='number',
                                     min=10, max=1000, value=200))
                      ])

nA_input = dbc.Row([dbc.Col(dcc.Markdown('$N_A$', id=_id('nA-label'), mathjax=True), md=2),
                    dbc.Col(dbc.Input(id = _id('nA-input'), type='number',
                                     min=0, max=50, value=10))
                    ])

nB_input = dbc.Row([dbc.Col(dcc.Markdown('$N_B$', id=_id('nB-label'), mathjax=True), md=2),
                    dbc.Col(dbc.Input(id = _id('nB-input'), type='number',
                                     min=0, max=50, value=10))
                    ])

generate_button = dbc.Button(_('generate'), id=_id('generate-button'), style={'margin-bottom':5})

commands = dbc.Container([dbc.Row([dbc.Col(nA_input),]),
                          dbc.Row([dbc.Col(nB_input),]),
                          dbc.Row([dbc.Col(steps_input),]),
                          dbc.Row([dbc.Col(generate_button),])
                         ])

graph = dcc.Graph(id=_id('plot'), config= {'displayModeBar': False})

def layout():
    layout = dbc.Container([
    header(),
    html.Hr(),
    dbc.Row([dbc.Col(commands, md=2), dbc.Col(graph, md=8),],
             align="center",)
    ],
    fluid=True,
    id =_id('layout')
    )
    return layout

######################
# specific callbacks #
######################

@callback([Output(_id('steps-label'), 'children'),
               Output(_id('generate-button'), 'children'),
               Output(_id('nA-label'), 'children'),
               Output(_id('nB-label'), 'children'),
              ],
              [Input(_id('steps-label'), 'children'),
               Input(_id('generate-button'), 'children'),
               Input(_id('nA-label'), 'children'),
               Input(_id('nB-label'), 'children'),
              ])
def setup_language_specific(*messages):
    return [_(m) for m in messages]

@callback(Output(_id('plot'), 'figure'),
              [Input(_id('generate-button'), 'n_clicks')],
              [State(_id('nA-input'), 'value'),
               State(_id('nB-input'), 'value'),
               State(_id('steps-input'), 'value')]
             )
def generate_animation(n_clicks, nA, nB, nsteps):
    '''
    set-up figure and generate frames for animation
    ''' 
    width = 100 # width of one box
    height = 100  # height of one box
    n = nA + nB
    model = Ehrenfest(nA, nB, nsteps, width, height)
    X, Y, fA, fB, hist, hist_fit = next(model)
    #Initialize figure with subplots
    fig = make_subplots(rows=2, cols=2,
                    column_widths=[0.8, 0.2],
                    row_heights=[0.5, 0.5],
                    specs=[[{'type': 'xy', 'rowspan': 2}, {'type': 'xy'}],
                          [            None             , {'type': 'xy'}]],
                   )
    # init data
    fig.update(data = [go.Scatter(x=X, y=Y, mode='markers', showlegend=False, xaxis='x1', yaxis='y1'),
                   go.Scatter(y=fA, name='A', xaxis='x2', yaxis='y2'),
                   go.Scatter(y=fB, name='B', xaxis='x2', yaxis='y2'),
                   go.Bar(x=hist[1]/n, y=hist[0], showlegend=False, xaxis='x3', yaxis='y3'),
                   go.Scatter(x=[], y=[], mode='lines', showlegend=False, xaxis='x3', yaxis='y3')
                  ]
              )
    
    # genrate frames for each step
    frames = []
    for X, Y, fA, fB, hist, hist_fit in model:
        frame = dict(name = str(len(frames)),
                     data = [go.Scatter(x=X, y=Y, mode='markers', showlegend=False),
                             go.Scatter(y=fA, name='A', mode='lines'),
                             go.Scatter(y=fB, name='B', mode='lines'),
                             go.Bar(x=hist[1]/n, y=hist[0], showlegend=False),
                             go.Scatter(x=hist[1]/n, y=hist_fit, mode='lines', showlegend=False)
                            ],
                     traces = [0, 1, 2, 3, 4])
        frames.append(frame)
    fig.update(frames=frames)
    
    # generate menu and input for animation
    updatemenus = [dict(type='buttons',
                        buttons=[dict(label='Play',
                        method='animate',
                        args=[[f'{k}' for k in range(nsteps)], 
                               dict(frame=dict(duration=50, redraw=False), 
                                    transition=dict(duration=0),
                                    #easing='linear',
                                    fromcurrent=True,
                                    #mode='immediate'
                                                       )])],
                        direction= 'left', 
                        pad=dict(r= 10, t=85), 
                        showactive =True, x= 0.1, y= 0, xanchor= 'right', yanchor= 'top')
                  ]

    sliders = [{'yanchor': 'top',
                'xanchor': 'left', 
                'currentvalue': {'font': {'size': 16}, 'prefix': _('Step: '), 'visible': True, 'xanchor': 'right'},
                'transition': {'duration': 500.0, 'easing': 'linear'},
                'pad': {'b': 10, 't': 50}, 
                'len': 0.9, 'x': 0.1, 'y': 0, 
                'steps': [{'args': [[k], {'frame': {'duration': 500.0, 'easing': 'linear', 'redraw': False},
                                          'transition': {'duration': 0, 'easing': 'linear'}}], 
                           'label': k, 'method': 'animate'} for k in range(nsteps)       
                         ]}]
              
    fig.update_layout(updatemenus=updatemenus, sliders=sliders)      

    # set up ranges for axes of various plots
    xdelta  = 2*width*0.05
    ydelta = height*0.05
    xrange = [-xdelta, 2*width+xdelta]
    yrange = [-ydelta, height+ydelta]
    fig.update_xaxes(range=xrange, autorange=False, showticklabels=False,
                     showgrid=False, showline=True, mirror=True, linewidth=2,
                     linecolor='black', row=1, col=1)
    fig.update_yaxes(range=yrange, autorange=False, showticklabels=False,
                     showgrid=False, showline=True, mirror=True, linewidth=2,
                     linecolor='black', row=1, col=1)
    
    pop_xrange = [0, nsteps]
    pop_yrange = [0, 1]
    fig.update_xaxes(range=pop_xrange, autorange=False, showline=True, mirror=True,
                     linewidth=1, linecolor='black', title=_('steps'), row=1, col=2)
    fig.update_yaxes(range=pop_yrange, autorange=False, showline=True, mirror=True,
                     linewidth=1, linecolor='black', title=_('fraction'), row=1, col=2)
    hist_range = [hist[1][0]/n, hist[1][-1]/n]
    fig.update_xaxes(range=hist_range, autorange=False, showline=True, mirror=True,
                     linewidth=1, linecolor='black', title=_('fluctuation'), row=2, col=2)
    fig.update_yaxes(range=[0, hist[0][1:].max()], showline=True, autorange=False, mirror=True,
                     linewidth=1, linecolor='black', title=_('probability'), row=2, col=2)
    
    fig.add_vline(x=width, line_width=2, row=1, col=1)
    fig.add_hline(y=0.5, line_dash='dash', row=1, col=2)
    fig.update_layout(width=1000, height=600, plot_bgcolor='rgb(255, 255, 255)', modebar_remove=['zoom', 'pan'])
    return fig


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