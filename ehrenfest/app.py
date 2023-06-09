import numpy as np
import dash
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from flask import Flask, request
from flask_babel import Babel, gettext
from plotly.subplots import make_subplots
from model import Ehrenfest

# define translator function
_ = gettext


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
app.config.update({'title': _('Ehrenfest model')})

#####################
# set up app layout #
#####################
title = html.H1(_('Ehrenfest model'), id='title')
subtitle = html.P(_('observe gas expansion'), id='subtitle')
info_button = dbc.Button(id='info-button', n_clicks=0, children='More info')
info_text = dcc.Markdown('   ', mathjax=True, id='info-text')
#info = dbc.Row([dbc.Col(info_button), dbc.Col(info_text)])

title_col = dbc.Col(dbc.Container([title, subtitle]), width='auto')
info_col = dbc.Col(dbc.Container([info_text, info_button]), width='auto')

header = dbc.Row([title_col, info_col])

steps_input = dbc.Row([dbc.Col(dbc.Label(_('steps'), id='steps-label'), md=2),
                       dbc.Col(dbc.Input(id = 'steps-input', type='number',
                                     min=10, max=1000, value=200))
                      ])

nA_input = dbc.Row([dbc.Col(dcc.Markdown('$N_A$', id='nA-label', mathjax=True), md=2),
                    dbc.Col(dbc.Input(id = 'nA-input', type='number',
                                     min=0, max=50, value=10))
                    ])

nB_input = dbc.Row([dbc.Col(dcc.Markdown('$N_B$', id='nB-label', mathjax=True), md=2),
                    dbc.Col(dbc.Input(id = 'nB-input', type='number',
                                     min=0, max=50, value=10))
                    ])

generate_button = dbc.Button(_('generate'), id='generate-button', style={'margin-bottom':5})

commands = dbc.Container([dbc.Row([dbc.Col(nA_input),]),
                          dbc.Row([dbc.Col(nB_input),]),
                          dbc.Row([dbc.Col(steps_input),]),
                          dbc.Row([dbc.Col(generate_button),])
                         ])

graph = dcc.Graph(id='plot', config= {'displayModeBar': False})

app.layout = dbc.Container([
                            header,
                            html.Hr(),
                            dbc.Row([dbc.Col(commands, md=2), dbc.Col(graph, md=8),],
                                     align="center",)
                            ], fluid=True)

    
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
        The **Ehrenfest model** is a simple representation of what happens during the expansion of a perfect gas. In this applet you can choose how many particles to put initially in box A and box B and how many steps of the model to simulate. After that, you can create the simulation by clicking on **generate** and observe what happens clicking on **play**. The plot  on the right top shows the fraction of particles, $f$, in the boxes ad each instant:  
        $$f_A = \frac{N_A}{N}$$
        while the plot a the right bottom shows the probability distribution of a **fluctuation**, at each instant. The fluctuation is the difference of population between the boxes divided by the total number of particles in the system:  
        
        $$fluct = \frac{N_A- N_B}{N}$$
        
        ''')
        button_text = _('less info')
    else:
        text = '   '
        button_text = _('more info')
    return button_text, text

@app.callback([Output('steps-label', 'children'),
               Output('generate-button', 'children'),
               Output('nA-label', 'children'),
               Output('nB-label', 'children'),
               Output('title', 'children'),
               Output('subtitle', 'children'),
              ],
              [Input('steps-label', 'children'),
               Input('generate-button', 'children'),
               Input('nA-label', 'children'),
               Input('nB-label', 'children'),
               Input('title', 'children'),
               Input('subtitle', 'children'),
              ])
def setup_language(*messages):
    return [_(m) for m in messages]

@app.callback(Output('plot', 'figure'),
              [Input('generate-button', 'n_clicks')],
              [State('nA-input', 'value'),
               State('nB-input', 'value'),
               State('steps-input', 'value')]
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
    app.run_server(debug=True)
