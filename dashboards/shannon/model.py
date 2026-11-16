"""Entropy of a fixed visible string, with individually labelled tiles.

Each uniformly shuffled labelled order is a microstate. The exact visible
string is a macrostate. W counts compatible microstates, not visible orders.
No Dash dependencies; counts are exact, logarithms use arbitrary-size integers.
"""

from collections import Counter
from dataclasses import dataclass
from itertools import islice, permutations
from math import factorial, log, log2, prod
import unicodedata

MAX_LENGTH = 50
MAX_MICROSTATES = 24
BOLTZMANN_CONSTANT = 1.380649e-23  # J/K, exact SI value


@dataclass(frozen=True)
class StringResult:
    text: str
    counts: tuple
    length: int
    multiplicity: int
    visible_orders: int
    entropy_over_kb: float
    entropy_j_k: float
    hidden_bits: float
    information_bits: float


def prepare_text(text, ignore_case=False, ignore_spaces=False,
                 ignore_punctuation=False):
    """NFC Unicode code points are symbols (not arbitrary visual graphemes).

    Bound the raw input as well as the processed text. Case conversion uses
    lower(), not casefold(), to avoid expanding characters such as German ß.
    """
    if not isinstance(text, str):
        raise TypeError('text must be a string')
    if len(text) > MAX_LENGTH:
        raise ValueError('too_long')
    text = unicodedata.normalize('NFC', text)
    if ignore_case:
        text = unicodedata.normalize('NFC', text.lower())
    if ignore_spaces:
        text = ''.join(c for c in text if not c.isspace())
    if ignore_punctuation:
        text = ''.join(c for c in text
                       if not unicodedata.category(c).startswith('P'))
    if len(text) > MAX_LENGTH:
        raise ValueError('too_long')
    return text


def analyse(text, **options):
    text = prepare_text(text, **options)
    if not text:
        raise ValueError('empty')
    counts = tuple(Counter(text).items())  # stable first-occurrence order
    length = len(text)
    w = prod(factorial(n) for _, n in counts)
    orders = factorial(length) // w
    # Compute log of the exact integers: avoids cancellation and gives exact
    # zero for all-identical/all-distinct cases, even at the length limit.
    entropy = log(w)
    return StringResult(text, counts, length, w, orders, entropy,
                        BOLTZMANN_CONSTANT * entropy, log2(w), log2(orders))


def compatible_microstates(text, limit=MAX_MICROSTATES):
    """Yield at most 24 compatible orders as tuples of (symbol, label).

    Depth-first permutation of labels within each character's fixed slots.
    Never enumerate N! permutations, build a Cartesian product pool, or
    materialize all W microstates before slicing.
    """
    if not isinstance(limit, int) or not 0 <= limit <= MAX_MICROSTATES:
        raise ValueError('limit must be between 0 and 24')
    if len(text) > MAX_LENGTH:
        raise ValueError('too_long')
    if not text or not limit:
        return
    groups = {}
    for position, character in enumerate(text):
        groups.setdefault(character, []).append(position)
    groups = list(groups.items())
    state = [None] * len(text)

    def visit(group):
        if group == len(groups):
            yield tuple(state)
            return
        character, positions = groups[group]
        for labels in permutations(range(1, len(positions) + 1)):
            for position, label in zip(positions, labels):
                state[position] = (character, label)
            yield from visit(group + 1)

    yield from islice(visit(0), limit)
