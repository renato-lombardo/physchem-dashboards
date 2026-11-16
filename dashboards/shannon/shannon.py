"""Shannon tab: fixed-string multiplicity and information in a shuffled bag."""

from pathlib import Path
import sys
import json

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, ALL, MATCH, callback, dcc, html
from dash.exceptions import PreventUpdate
from flask import request
from flask_babel import Babel, gettext
import plotly.graph_objects as go
from plotly.colors import qualitative

if __name__ == '__main__':
    # Reuse the repository utility without absolute symlinks or copied code.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from model import (analyse, compatible_microstates, MAX_LENGTH,
                       MAX_MICROSTATES)
else:
    from .model import (analyse, compatible_microstates, MAX_LENGTH,
                        MAX_MICROSTATES)
from utilities import _id, common_setup

_ = gettext
title = 'Shannon'
subtitle = _('Explore multiplicity, entropy and information in a string of tiles')
info = _(r'''Put the tiles of each string into its own bag and draw all of them
at random, without replacement. Individual tiles have hidden labels.
The **macrostate** is the exact visible string; a **microstate** specifies
the identities of all its tiles, in that order.

$$W=\prod_i n_i!,\qquad S_B=k_B\ln W$$

All $N!$ labelled orders are equally likely. The probability of drawing
the specified visible string is $P=W/N!$, so its **information content**, also called **surprisal**, is

$$I=-\log_2 P=\log_2(N!/W).$$

The stacked bars split $\log_2(N!)$ into hidden tile identities
($\log_2 W$) and information content ($I$).
In this uniform bag model, the Shannon entropy of the distribution of
visible sequences equals $I$. This is not the single-letter expression
$-\sum_i p_i\log_2p_i$.

''')
order = 5.5  # immediately after Ehrenfest (5), before Carnot (6)
header, setup_language_general, show_info = common_setup(title, subtitle, info)
COLORS = qualitative.Plotly
EXAMPLES = ('otto', 'atto', 'alti', 'AAAAA', 'AMORE',
            'TTAGGG', 'TTAGGGTTAGGG', 'AAAAAAAAAAAA')


def pid(kind, uid):
    return {'type': _id(kind), 'uid': uid}


def color(uid):
    return COLORS[int(uid) % len(COLORS)]


def symbol(character):
    """Give whitespace and controls an explicit, visible representation."""
    return {' ': '␠', '\n': '↵', '\t': '⇥', '\r': '␍'}.get(
        character, character if character.isprintable() else repr(character)[1:-1])


def integer(value):
    return f'{value:,}'.replace(',', ' ')


def controls_card_factory(uid, text=''):
    return dbc.Card([
        dbc.Row([
            dbc.Col(html.Strong(_('String %(number)s', number=uid + 1))),
            dbc.Col(dbc.Button(_('Delete'), id=pid('delete', uid),
                               n_clicks=0, size='sm', outline=True,
                               color='secondary'), width='auto'),
        ], align='center', className='mb-2'),
        dbc.Label(_('Text (maximum 50 characters)'), html_for=json.dumps(pid('text', uid), sort_keys=True, separators=(',', ':'))),
        # Pattern IDs are needed for callbacks; label the field accessibly too.
        dcc.Input(id=pid('text', uid), type='text', value=text,
                  maxLength=MAX_LENGTH, debounce=True,
                     style={'width': '100%', 'minHeight': '38px',
                            'fontFamily': 'monospace'}),
        html.Small(_('Press Enter or leave the field to update the results.'),
                   className='text-muted'),
        html.Div(id=pid('counter', uid), className='small text-muted mb-2'),
        dcc.Dropdown(id=pid('example', uid),
                     options=[{'label': text, 'value': text} for text in EXAMPLES],
                     placeholder=_('Choose an example'), clearable=True),
        html.Div(id=pid('result', uid), className='mt-3'),
    ], id=pid('card', uid), body=True,
        style={'borderColor': color(uid), 'borderWidth': '2px',
               'marginBottom': '12px'})


def layout():
    return dbc.Container([
        header(), html.Hr(),
        dbc.Alert(_(
            'Each string defines its own bag. W counts labelled microstates '
            'compatible with that exact visible string. I measures the '
            'information content of the exact sequence drawn at random, without replacement.'),
            color='light'),
        dbc.Row([
            dbc.Col([
                dbc.Button(_('Add string'), id=_id('add'), n_clicks=0,
                           className='mb-3'),
                dbc.Checklist(id=_id('options'), value=[], options=[
                    {'label': _('Ignore case'), 'value': 'case'},
                    {'label': _('Ignore whitespace'), 'value': 'spaces'},
                    {'label': _('Ignore punctuation'), 'value': 'punctuation'},
                ], className='mb-3'),
                html.Small(_(
                    'Accents are preserved. Symbols are NFC-normalized Unicode '
                    'code points; complex emoji may contain several symbols.'),
                    className='text-muted'),
                html.Hr(),
                dcc.Store(id=_id('next-id'), data=2),
                html.Div([controls_card_factory(0, 'otto'),
                          controls_card_factory(1, 'atto')],
                         id=_id('cards')),
            ], lg=4, xl=3),
            dbc.Col([
                dbc.RadioItems(id=_id('scale'), value='total', inline=True,
                               options=[{'label': _('Total'), 'value': 'total'},
                                        {'label': _('Per character'), 'value': 'character'}]),
                dcc.Graph(id=_id('plot'), config={'displaylogo': False}),
                html.Small(_(
                    'The two segments add up to log₂(N!). Equal-length strings '
                    'have equal totals.'),
                    className='text-muted'),
                html.H4(_('Comparison'), className='mt-4'),
                html.Div(id=_id('comparison')),
            ], lg=8, xl=9),
        ]),
    ], fluid=True, id=_id('layout'))


@callback(Output(_id('cards'), 'children'), Output(_id('next-id'), 'data'),
          Input(_id('add'), 'n_clicks'),
          Input({'type': _id('delete'), 'uid': ALL}, 'n_clicks'),
          State(_id('cards'), 'children'), State(_id('next-id'), 'data'),
          prevent_initial_call=True)
def update_cards(add_clicks, delete_clicks, cards, next_id):
    trigger = dash.ctx.triggered_id
    cards = list(cards or [])
    if trigger == _id('add') and add_clicks:
        return cards + [controls_card_factory(next_id)], next_id + 1
    if isinstance(trigger, dict) and dash.ctx.triggered[0]['value']:
        return [card for card in cards
                if card['props']['id']['uid'] != trigger['uid']], next_id
    raise PreventUpdate


@callback(Output({'type': _id('text'), 'uid': MATCH}, 'value'),
          Input({'type': _id('example'), 'uid': MATCH}, 'value'),
          prevent_initial_call=True)
def choose_example(value):
    if value is None:
        raise PreventUpdate
    return value


def tile(character, label, palette):
    return html.Span([symbol(character), html.Sub(str(label))],
                     title=repr(character),
                     style={'display': 'inline-block', 'padding': '3px 6px',
                            'margin': '2px', 'borderRadius': '4px',
                            'border': f'1px solid {palette[character]}',
                            'borderBottomWidth': '3px', 'backgroundColor': '#fff',
                            'color': '#212529', 'fontFamily': 'monospace',
                            'whiteSpace': 'pre'})


def result_panel(result):
    palette = {character: COLORS[i % len(COLORS)]
               for i, (character, _) in enumerate(result.counts)}
    microstates = list(compatible_microstates(result.text))
    states = [html.Div([tile(c, label, palette) for c, label in state],
                       style={'padding': '4px 0', 'borderBottom': '1px solid #eee'})
              for state in microstates]
    count_text = _('Showing %(shown)s of %(total)s compatible microstates',
                   shown=len(microstates), total=integer(result.multiplicity))
    return [
        html.Div([html.Strong(_('Analysed string: ')), html.Code(repr(result.text))],
                 style={'overflowWrap': 'anywhere'}),
        html.Div(' · '.join(f'{repr(c)} × {n}' for c, n in result.counts),
                 className='small text-muted', style={'overflowWrap': 'anywhere'}),
        html.Div([html.Strong('W = '), integer(result.multiplicity)],
                 style={'overflowWrap': 'anywhere'}),
        html.Div(f'Sᴮ / kᴮ = {result.entropy_over_kb:.6g}'),
        html.Div(f'Sᴮ = {result.entropy_j_k:.6g} J/K'),
        html.Div([_('Information content: '), f'I = {result.information_bits:.6g} bit']),
        html.Small('P = 1 / ' + integer(result.visible_orders),
                   className='text-muted', style={'overflowWrap': 'anywhere'}),
        html.Details([
            html.Summary(_('Compatible microstates'), className='mt-2'),
            html.P(count_text, className='small text-muted mt-2'),
            html.Small(_('Subscripts identify individual tiles; the visible '
                         'character order never changes.'), className='text-muted'),
            html.Div(states, style={'maxHeight': '440px', 'overflowY': 'auto'}),
        ]),
    ]


def comparison_table(rows):
    headings = [_('String'), 'N', _('Distinct symbols'), 'W', 'Sᴮ / kᴮ',
                'Sᴮ (J/K)', _('Information content I (bit)')]
    body = []
    for uid, result in rows:
        cells = [html.Code(repr(result.text)), result.length, len(result.counts),
                 integer(result.multiplicity), f'{result.entropy_over_kb:.6g}',
                 f'{result.entropy_j_k:.6g}', f'{result.information_bits:.6g}']
        body.append(html.Tr([html.Td(value, style={'overflowWrap': 'anywhere'})
                             for value in cells],
                            style={'borderLeft': f'4px solid {color(uid)}'}))
    return dbc.Table([html.Thead(html.Tr([html.Th(h) for h in headings])),
                      html.Tbody(body)], bordered=True, striped=True,
                     hover=True, responsive=True, size='sm')


@callback(Output(_id('plot'), 'figure'), Output(_id('comparison'), 'children'),
          Output({'type': _id('result'), 'uid': ALL}, 'children'),
          Output({'type': _id('counter'), 'uid': ALL}, 'children'),
          Input({'type': _id('text'), 'uid': ALL}, 'value'),
          Input(_id('options'), 'value'), Input(_id('scale'), 'value'),
          State({'type': _id('text'), 'uid': ALL}, 'id'))
def update_results(texts, selected, scale, identifiers):
    selected = selected or []
    options = dict(ignore_case='case' in selected,
                   ignore_spaces='spaces' in selected,
                   ignore_punctuation='punctuation' in selected)
    rows, panels, counters = [], [], []
    for text, identifier in zip(texts, identifiers):
        text = text or ''
        counters.append(_('%(number)s/50 characters', number=len(text)))
        try:
            result = analyse(text, **options)
        except ValueError as error:
            message = (_('Maximum length: 50 characters.') if str(error) == 'too_long'
                       else _('Enter a string with at least one retained character.'))
            panels.append(dbc.Alert(message, color='secondary', className='mt-2'))
            continue
        rows.append((identifier['uid'], result))
        panels.append(result_panel(result))

    figure = go.Figure()
    if rows:
        labels = [str(uid) for uid, _ in rows]
        per_character = scale == 'character'
        divisors = [r.length if per_character else 1 for _, r in rows]
        shades = [color(uid) for uid, _ in rows]
        custom = [[r.text, r.length] for _, r in rows]
        for name, values, opacity, pattern in [
            ('log₂ W',
             [r.hidden_bits / d for (_, r), d in zip(rows, divisors)], .4, '/'),
            (_('Information content: I'),
             [r.information_bits / d for (_, r), d in zip(rows, divisors)], 1, ''),
        ]:
            figure.add_trace(go.Bar(name=name, x=values, y=labels, orientation='h',
                                   marker=dict(color=shades, opacity=opacity,
                                               pattern_shape=pattern),
                                   customdata=custom,
                                   hovertemplate='%{customdata[0]}<br>N = %{customdata[1]}'
                                                 '<br>%{x:.6g}<extra>%{fullData.name}</extra>'))
        figure.update_yaxes(tickmode='array', tickvals=labels,
                            type='category',
                            ticktext=[_('String %(number)s', number=uid + 1) + ': ' +
                                      repr(r.text[:18] + ('…' if r.length > 18 else ''))
                                      for uid, r in rows], autorange='reversed')
    else:
        figure.add_annotation(text=_('Add a string to begin the comparison.'),
                              x=.5, y=.5, xref='paper', yref='paper', showarrow=False)
    figure.update_layout(template='plotly_white', barmode='stack',
                         height=max(360, 100 + 85 * len(rows)),
                         xaxis_title=_('bit / character') if scale == 'character' else 'bit',
                         xaxis=dict(rangemode='tozero'),
                         legend=dict(orientation='h', y=-.25),
                         margin=dict(l=30, r=20, t=30, b=110))
    table = comparison_table(rows) if rows else html.P(_('No valid strings to compare.'))
    return figure, table, panels, counters


translation = 'dashboards/shannon/translations'
if __name__ == '__main__':
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    catalog = str(Path(__file__).resolve().parent / 'translations')
    app.server.config['BABEL_TRANSLATION_DIRECTORIES'] = catalog
    Babel(app.server, locale_selector=lambda: request.accept_languages.best_match(['en', 'it']))
    app.layout = layout
    app.run_server(debug=True, host='127.0.0.1', port=5000)
else:
    dash.register_page(__name__, path='/shannon', title=title, name=title,
                       subtitle=subtitle, info=info, order=order,
                       translation=translation)
