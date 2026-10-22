"""Exploration calculations, mirrored in analysis.js. Roster rules stay separate."""
import math
import re
from decimal import Decimal, ROUND_HALF_UP

FIELDS = {'bust': 'bust_cm', 'waist': 'waist_cm', 'hip': 'hip_cm',
          'thigh': 'thigh_cm', 'height': 'stature_cm', 'underbust': 'band_cm'}
WEIGHTS = {'bust': .25, 'waist': .2, 'hip': .2, 'thigh': .15, 'height': .2, 'underbust': 0}
CUP_BASE = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7,
            'H': 8, 'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13}


def size_parts(size):
    match = re.fullmatch(r'(\d+)\s*([A-Za-z]+)', size or '')
    if not match:
        return None
    return {'cup': match[2].upper(), 'band': int(match[1])}


def cup_size(size):
    parts = size_parts(size)
    if not parts or parts['cup'][0] not in CUP_BASE:
        return None
    cup = parts['cup']
    return {**parts, 'score': CUP_BASE[cup[0]] * 10000 + (1000 if len(cup) == 1 else 0) + parts['band']}


def cup_distribution(roster, system='uk'):
    system = system if system in ('uk', 'us', 'eu') else 'uk'
    groups = {}
    for record in roster:
        size = (cup_size if system == 'uk' else size_parts)(record.get(system))
        if size:
            groups[size['cup']] = groups.get(size['cup'], 0) + 1
    bins = [{'cup': cup, 'count': count} for cup, count in groups.items()]
    bins.sort(key=lambda b: cup_size('0' + b['cup'])['score'] if system == 'uk'
              else ord(b['cup'][0]) * 1000 + len(b['cup']))
    peak = max(groups.values(), default=0)
    return {'count': sum(groups.values()), 'bins': bins,
            'modes': [b['cup'] for b in bins if b['count'] == peak]}


def percentage(value, height):
    return value / height * 100 if value is not None and height and height > 0 else None


def cup_matrix(roster, system='uk'):
    system = system if system in ('uk', 'us', 'eu') else 'uk'
    sizes = [(d, (cup_size if system == 'uk' else size_parts)(d.get(system))) for d in roster]
    sizes = [(d, size) for d, size in sizes if size]
    bands = sorted({size['band'] for _, size in sizes})
    cups = [b['cup'] for b in cup_distribution(roster, system)['bins']]
    cells = [{'band': band, 'cup': cup,
              'slugs': [d['slug'] for d, size in sizes if size['band'] == band and size['cup'] == cup]}
             for band in bands for cup in cups]
    return {'bands': bands, 'cups': cups, 'cells': cells}


def metric_value(record, key, basis='raw', target=160):
    value = record.get(FIELDS[key])
    if key == 'height' or basis == 'raw':
        return value
    height = record.get('stature_cm')
    if value is None or not height or height <= 0:
        return None
    return value / height * (target if basis == 'scaled' else 100)


def displayed(value):
    """Match JavaScript Number(value.toFixed(1)), including binary halfway cases."""
    return float(Decimal.from_float(float(value)).quantize(Decimal('.1'), rounding=ROUND_HALF_UP)) if value is not None else None


def difference(value, reference):
    return value - reference if value is not None and reference is not None else None


def outcome(left, right):
    a, b = displayed(left), displayed(right)
    return None if a is None or b is None else 'equal' if a == b else 'higher' if b > a else 'lower'


def game_outcome(left, right, key, basis='raw', unit='cm'):
    def value(record):
        if key == 'cup':
            size = cup_size(record.get('uk'))
            return size['score'] if size else None
        result = metric_value(record, key, basis)
        return result / 2.54 if result is not None and unit == 'in' and (basis != 'height' or key == 'height') else result
    return outcome(value(left), value(right))


def matches(roster, source, weights=None, basis='raw'):
    weights = WEIGHTS if weights is None else weights
    spans = {}
    for key in FIELDS:
        values = [metric_value(d, key, basis) for d in roster]
        values = [v for v in values if v is not None]
        spans[key] = (max(values) - min(values) or 1) if values else 1
    results = []
    for d in roster:
        if d['slug'] == source['slug']:
            continue
        score = total = 0
        components = []
        for key in FIELDS:
            weight = weights.get(key, 0)
            if not math.isfinite(weight) or weight <= 0:
                continue
            a, b = metric_value(source, key, basis), metric_value(d, key, basis)
            if a is None or b is None:
                continue
            diff = abs(a - b)
            weighted = weight * diff / spans[key]
            score += weighted
            total += weight
            components.append({'key': key, 'difference': diff, 'weight': weight, 'contribution': weighted})
        if total:
            results.append({'d': d, 'score': score / total,
                            'components': [{**c, 'weight': c['weight'] / total,
                                            'contribution': c['contribution'] / total} for c in components]})
    return sorted(results, key=lambda x: x['score'])


def distribution(values, count=10):
    values = sorted(v for v in values if v is not None and math.isfinite(v))
    if not values:
        return {'count': 0, 'median': None, 'bins': []}
    lo, hi, n = values[0], values[-1], len(values)
    size = 1 if lo == hi else count
    step = (hi - lo) / size
    bins = [{'lo': lo + i * step, 'hi': lo + (i + 1) * step, 'count': 0} for i in range(size)]
    bins[-1]['hi'] = hi
    for value in values:
        index = min(size - 1, int((value - lo) / step)) if step else 0
        bins[index]['count'] += 1
    return {'count': n, 'median': (values[(n - 1) // 2] + values[n // 2]) / 2, 'bins': bins}


def bin_index(value, bins):
    if value is None or not math.isfinite(value) or not bins:
        return -1
    lo, hi = bins[0]['lo'], bins[-1]['hi']
    if value < lo or value > hi:
        return -1
    return 0 if hi == lo else min(len(bins) - 1, int((value - lo) / ((hi - lo) / len(bins))))
