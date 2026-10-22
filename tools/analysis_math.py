"""Exploration calculations, mirrored in analysis.js. Roster rules stay separate."""
import math
from decimal import Decimal, ROUND_HALF_UP

FIELDS = {'bust': 'bust_cm', 'waist': 'waist_cm', 'hip': 'hip_cm',
          'thigh': 'thigh_cm', 'height': 'stature_cm', 'underbust': 'band_cm'}
WEIGHTS = {'bust': .25, 'waist': .2, 'hip': .2, 'thigh': .15, 'height': .2, 'underbust': 0}


def percentage(value, height):
    return value / height * 100 if value is not None and height and height > 0 else None


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
        for key in FIELDS:
            weight = weights.get(key, 0)
            if not math.isfinite(weight) or weight <= 0:
                continue
            a, b = metric_value(source, key, basis), metric_value(d, key, basis)
            if a is None or b is None:
                continue
            score += weight * abs(a - b) / spans[key]
            total += weight
        if total:
            results.append({'d': d, 'score': score / total})
    return sorted(results, key=lambda x: x['score'])


def distribution(values, count=10):
    values = sorted(v for v in values if v is not None and math.isfinite(v))
    if not values:
        return {'count': 0, 'median': None, 'bins': []}
    lo, hi, n = values[0], values[-1], len(values)
    size = 1 if lo == hi else count
    step = (hi - lo) / size
    bins = [{'lo': lo + i * step, 'hi': lo + (i + 1) * step, 'count': 0} for i in range(size)]
    for value in values:
        index = min(size - 1, int((value - lo) / step)) if step else 0
        bins[index]['count'] += 1
    return {'count': n, 'median': (values[(n - 1) // 2] + values[n // 2]) / 2, 'bins': bins}
