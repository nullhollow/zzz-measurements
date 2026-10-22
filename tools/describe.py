import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

data = json.load(open(ROOT/'tools/data.json'))
by_key = {d['name']: d for d in data}
# stature baseline for the profile text, using head height where the chart counts an appendage
ROSTER_AVG = sum(d['stature_cm'] for d in data) / len(data)
# rank by stature (1 = tallest) so the "tallest" claim matches the actual chart position;
# tied statures share the better rank, hence the "among the tallest" wording for the top group
_HEIGHTS = [d['stature_cm'] for d in data]
H_TOTAL = len(data)
H_RANK = {d['name']: 1 + sum(1 for x in _HEIGHTS if x > d['stature_cm']) for d in data}


def ordinal(n):
    if 10 <= n % 100 <= 20: suf = 'th'
    else: suf = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suf}"

def rel_bust(p):
    if p is None: return "hard to place"
    if p >= 0.85: return "among the largest bust measurements on the chart"
    if p >= 0.66: return "clearly above the roster average"
    if p >= 0.34: return "close to the roster average"
    if p >= 0.15: return "on the modest side for the chart"
    return "among the smallest bust measurements here"

CUP_PHRASE = {
  'A-B':  "a modest A–B tier",
  'C-D':  "a middle-of-the-road C–D tier",
  'DD-E': "a full DD–E tier",
  'F-G':  "a heavy F–G tier",
  'GG+':  "one of the chart's heaviest GG+ tiers",
}
WAIST_PHRASE = {
  'low': "one of the trimmer midsections in the set",
  'avg': "a middling midsection by this set's standards",
  'high': "a fuller midsection than most of the roster",
}
HIP_WORD   = {'low':"compact",'avg':"average-width",'high':"wide"}
THIGH_WORD = {'low':"slim",'avg':"average",'high':"thick"}

def rankword(p):
    if p is None: return "unranked"
    if p >= 0.85: return f"top {max(1, round((1-p)*100))}% of the roster"
    if p <= 0.15: return f"bottom {max(1, round(p*100))}% of the roster"
    return "mid-pack for the roster"

def describe(d, unit, compare=None):
    cmu = (unit == 'cm')
    word = 'cm' if cmu else 'in'

    def v(in_key, cm_key, dec=1):
        raw = d[cm_key] if cmu else d[in_key]
        if raw is None: return '—'
        s = f"{raw:.{dec}f}".rstrip('0').rstrip('.')
        return f"{s} {word}"

    n = d['display']; cmv = d['cm']; ft = d.get('ftin')
    hg = d['height_group']
    if d['stature_basis'] == 'head':
        gap = d['stature_cm'] - ROSTER_AVG
        where = 'just under' if gap < -2 else ('above' if gap > 2 else 'right around')
        frame = (f"{n} is charted at {cmv:g} cm ({ft}), but that figure counts her ears: at head height "
                 f"she stands about {d['stature_cm']:g} cm ({d['ftin_stature']}), {where} the roster average.")
    elif hg == 'Tall':
        r = H_RANK.get(d.get('variant_of') or d['name'], H_TOTAL)
        if r <= 3:
            frame = f"{n} is among the tallest figures on the chart at {cmv:g} cm ({ft})."
        elif r <= 8:
            frame = (f"{n} is one of the taller figures here, {ordinal(r)} tallest of {H_TOTAL}, "
                     f"at {cmv:g} cm ({ft}).")
        else:
            frame = (f"{n} measures {cmv:g} cm ({ft}), above the roster average at "
                     f"{ordinal(r)} tallest of {H_TOTAL}.")
    else:
        frame = {
            'Petite': f"{n} measures just {cmv:g} cm ({ft}), one of the most compact frames on the chart.",
            'Mid':    f"{n} measures {cmv:g} cm ({ft}), right around the roster average.",
        }[hg]
    bust = f"Her {v('bust_in','bust_cm')} bust (UK {d['uk']}) is {rel_bust(d['p_bust_cm'])}."
    waist = (f"The waist comes in at {v('waist_in','waist_cm')} (waist-to-height {d['whtr']:.2f}), "
             f"{WAIST_PHRASE[d['waist_level']]}.")
    if d['thigh_cm'] is not None:
        hips = (f"Below that, {HIP_WORD[d['hip_level']]} hips ({v('hip_in','hip_cm')}) pair with "
                f"{THIGH_WORD[d['thigh_level']]} {v('thigh_in','thigh_cm')} thighs "
                f"({rankword(d['p_thigh_cm'])} by thigh circumference).")
    else:
        hips = (f"Below that, hips read {HIP_WORD[d['hip_level']]} at {v('hip_in','hip_cm')}; "
                f"no reliable thigh measurement exists for her.")
    b, h = d['bust_cm'], d['hip_cm']
    balance_text = ("The chest carries noticeably more visual weight than the hips" if b > h * 1.10
                    else "The hips carry more visual weight than the chest" if h > b * 1.10
                    else "Chest and hips are fairly evenly matched")
    bw = b / d['waist_cm'] if b and d['waist_cm'] else 0
    hw = h / d['waist_cm'] if h and d['waist_cm'] else 0
    bhi = min(b, h) / max(b, h)
    article = 'an' if d['shape'] == 'Hourglass' else 'a'
    shape = (f"Put together, she reads as {article} {d['shape'].lower()} silhouette "
             f"(bust/waist {bw:.2f}, hip/waist {hw:.2f}, bust–hip balance {bhi*100:.0f}%): {balance_text}.")
    parts = [frame, bust, waist, hips, shape]
    if compare is None and d.get('variant_of'):
        compare = by_key.get(d['variant_of'])
    if compare is not None:
        b = compare
        if cmu:
            dB = (d['bust_cm'] or 0) - (b['bust_cm'] or 0)
            dW = (d['waist_cm'] or 0) - (b['waist_cm'] or 0)
            dH = (d['hip_cm'] or 0) - (b['hip_cm'] or 0)
            u = 'cm'
        else:
            dB = d['bust_in'] - b['bust_in']
            dW = d['waist_in'] - b['waist_in']
            dH = d['hip_in'] - b['hip_in']
            u = 'in'
        if max(abs(dB), abs(dW), abs(dH)) >= (1.2 if cmu else 0.5):
            parts.append(f"Versus her standard model this outfit reads {dB:+.1f} {u} bust, "
                         f"{dW:+.1f} {u} waist, {dH:+.1f} {u} hips.")
    notes = d['notes']
    if d['stature_basis'] == 'head' and notes.lower().startswith('height includes ears'):
        notes = ''          # already spelled out in the first sentence
    if notes:
        parts.append(f"Chart note: {notes}.")
    return ' '.join(parts)

BALANCE_WORD = {'top': "top-heavy", 'bottom': "bottom-heavy", 'even': "balanced"}


def read_line(d):
    """One short, symbol-friendly sentence: the same commentary the prose carries, compressed."""
    frame = {'Petite': "compact", 'Mid': "mid-height", 'Tall': "tall"}[d['height_group']]
    bits = []
    if d['p_bust_cm'] is not None:
        if d['p_bust_cm'] >= 0.7: bits.append("full bust")
        elif d['p_bust_cm'] <= 0.3: bits.append("modest bust")
    if d['p_waist_cm'] is not None:
        if d['p_waist_cm'] >= 0.7: bits.append("full waist")
        elif d['p_waist_cm'] <= 0.3: bits.append("trim waist")
    if d['p_hip_cm'] is not None:
        if d['p_hip_cm'] >= 0.7: bits.append("wide hips")
        elif d['p_hip_cm'] <= 0.3: bits.append("narrow hips")
    if d['thigh_cm'] is not None:
        if d['p_thigh_cm'] is not None and d['p_thigh_cm'] >= 0.66: bits.append("thick thighs")
        elif d['p_thigh_cm'] is not None and d['p_thigh_cm'] <= 0.33: bits.append("slim thighs")
    line = f"{frame} frame"
    if bits:
        line += " with " + ", ".join(bits)
    line += f". {d['shape']} silhouette, {BALANCE_WORD[d['balance']]} proportions."
    return line


def build_tags(d):
    return {
        'height': d['height_group'],
        'bust': d['cup_group'],
        'waist': {'low':'Cinched','avg':'Average','high':'Fuller'}[d['waist_level']],
        'hips': HIP_WORD[d['hip_level']].capitalize(),
        'thighs': (THIGH_WORD[d['thigh_level']].capitalize() if d['thigh_cm'] is not None else 'n/a'),
        'shape': d['shape'],
        'balance': {'top':'Top-heavy','bottom':'Bottom-heavy','even':'Balanced'}[d['balance']],
    }

# ---------------------------------------------------------------------------
# Localized profiles
# ---------------------------------------------------------------------------
# The wording below is written for each language rather than translated line by
# line. Names come from the official HoYoverse character pages via
# tools/localized_names.json.
NOTE_JA = {
    'Torso measurements approximated due to clothing and a lack of data on rabbit thiren physiology':
        '服装のため胴体は概算。ラビット・シアンの体型データが少ないため',
    'Chest approximated due to clothing': '服装のため胸囲は概算',
    'Hip approximated, thigh impossible to measure': 'ヒップは概算、太ももは計測不能',
    'Waist and hip approximated': 'ウエストとヒップは概算',
    'Hip approximated, clothing too baggy for accurate reading':
        '服装がゆったりしているためヒップは概算',
    'Height includes ears': '身長は耳を含む',
    'SAnby used for measurements, more visible geometry available':
        '計測にはSAnbyを使用（形状データが多いほう）',
    'Chest approximated due to armor': '鎧のため胸囲は概算',
    'Measurements use the Nocturne of Light outfit; standard-model values are not used.':
        '「Nocturne of Light」の衣装で計測。標準モデルの数値は使用していない',
    'TBC': '未確定',
}
NOTE_ZH = {
    'Torso measurements approximated due to clothing and a lack of data on rabbit thiren physiology':
        '受服装影响，躯干数据为估算；兔希人体型资料较少',
    'Chest approximated due to clothing': '受服装影响，胸围为估算',
    'Hip approximated, thigh impossible to measure': '臀围为估算，大腿无法测量',
    'Waist and hip approximated': '腰围和臀围为估算',
    'Hip approximated, clothing too baggy for accurate reading':
        '服装较宽松，臀围为估算',
    'Height includes ears': '身高包含耳朵',
    'SAnby used for measurements, more visible geometry available':
        '测量使用 SAnby（几何数据更完整）',
    'Chest approximated due to armor': '受铠甲影响，胸围为估算',
    'Measurements use the Nocturne of Light outfit; standard-model values are not used.':
        '采用「Nocturne of Light」服装的数据，未使用标准模型数值',
    'TBC': '待确认',
}
REL_BUST_JA = (
    (0.85, 'チャートでもトップクラスのボリューム'),
    (0.66, 'ロスター平均をはっきり上回る'),
    (0.34, 'ロスター平均とほぼ同じ'),
    (0.15, 'チャートでは控えめなほう'),
    (0.00, 'チャートでも小さいほう'),
)
REL_BUST_ZH = (
    (0.85, '在全榜里属于非常抢眼的尺寸'),
    (0.66, '明显高于全榜平均'),
    (0.34, '和全榜平均差不多'),
    (0.15, '在全榜里偏含蓄'),
    (0.00, '在全榜里属于偏小的一档'),
)
WAIST_JA = {'low': 'ロスターでも細め', 'avg': 'このメンバーでは平均的', 'high': 'ロスターの多くよりもしっかりめ'}
WAIST_ZH = {'low': '在全榜里算很细的腰', 'avg': '在这批角色里属于中等', 'high': '比大多数角色更有肉感'}
HIP_JA = {'low': 'コンパクトな', 'avg': '平均的な', 'high': '広めの'}
HIP_ZH = {'low': '较窄的', 'avg': '中等宽度的', 'high': '较宽的'}
HIP_SENT_JA = {'low': 'コンパクトめです', 'avg': '平均的です', 'high': '広めです'}
HIP_SENT_ZH = {'low': '偏窄', 'avg': '宽度中等', 'high': '偏宽'}
THIGH_JA = {'low': '細めの', 'avg': '平均的な', 'high': '太めの'}
THIGH_ZH = {'low': '纤细的', 'avg': '中等', 'high': '丰满的'}
SHAPE_JA = {'Hourglass': '砂時計型', 'Balanced': 'バランス型', 'Straight': '直線型'}
SHAPE_ZH = {'Hourglass': '沙漏型', 'Balanced': '匀称型', 'Straight': '直线型'}
BALANCE_JA = {'top': 'やや上半身寄り', 'bottom': 'やや下半身寄り', 'even': '上下のバランスが取れています'}
BALANCE_ZH = {'top': '上半身更有分量', 'bottom': '下半身更有分量', 'even': '上下比较均衡'}
TAG_JA = {
    'Petite': '小柄', 'Mid': '中背', 'Tall': '高身長',
    'Cinched': 'くびれ', 'Average': '平均', 'Fuller': 'しっかり',
    'Compact': 'コンパクト', 'Average-width': '平均的', 'Wide': '広め',
    'Slim': '細め', 'Thick': '太め',
    'Hourglass': '砂時計型', 'Balanced': 'バランス型', 'Straight': '直線型',
    'Top-heavy': '上半身寄り', 'Bottom-heavy': '下半身寄り', 'n/a': '計測なし',
}
TAG_ZH = {
    'Petite': '娇小', 'Mid': '中等', 'Tall': '高挑',
    'Cinched': '纤细', 'Average': '适中', 'Fuller': '丰满',
    'Compact': '窄胯', 'Average-width': '适中', 'Wide': '宽胯',
    'Slim': '纤细', 'Thick': '丰满',
    'Hourglass': '沙漏型', 'Balanced': '匀称型', 'Straight': '直线型',
    'Top-heavy': '上围偏重', 'Bottom-heavy': '下围偏重', 'n/a': '无数据',
}
FRAME_JA = {'Petite': '小柄な体格', 'Mid': '中背', 'Tall': '高身長'}


def shape_balance(d):
    b, h = d['bust_cm'], d['hip_cm']
    return 'top' if b > h * 1.10 else ('bottom' if h > b * 1.10 else 'even')
FRAME_ZH = {'Petite': '个子娇小', 'Mid': '中等身高', 'Tall': '身材高挑'}


def lname(d, lang):
    return d.get('name_ja' if lang == 'ja' else 'name_zh') or d['display']


def lnum(v, dec=1):
    if v is None:
        return '—'
    s = f'{v:.{dec}f}'
    return s.rstrip('0').rstrip('.')


def lv(d, unit, lang, in_key, cm_key, dec=1):
    raw = d[cm_key] if unit == 'cm' else d[in_key]
    if raw is None:
        return '—'
    s = lnum(raw, dec)
    if unit == 'cm':
        return f'{s}cm' if lang == 'ja' else f'{s}厘米'
    return f'{s}インチ' if lang == 'ja' else f'{s}英寸'


def rel_bust_l(p, table):
    if p is None:
        return 'うまく位置づけにくい' if table is REL_BUST_JA else '不太好判断'
    for cut, text in table:
        if p >= cut:
            return text
    return table[-1][1]


def rank_l(p, lang):
    if p is None:
        return '順位なし' if lang == 'ja' else '没有排名'
    if p >= 0.85:
        return f"ロスター上位{max(1, round((1-p)*100))}%" if lang == 'ja' else f"排在全榜前{max(1, round((1-p)*100))}%"
    if p <= 0.15:
        return f"ロスター下位{max(1, round(p*100))}%" if lang == 'ja' else f"排在全榜后{max(1, round(p*100))}%"
    return 'ロスター中位' if lang == 'ja' else '排在全榜中段'


def note_l(d, lang):
    note = d.get('notes') or ''
    if not note:
        return ''
    if d['stature_basis'] == 'head' and note.lower().startswith('height includes ears'):
        return ''
    return (NOTE_JA if lang == 'ja' else NOTE_ZH).get(note, note)


def describe_ja(d, unit, compare=None):
    n = lname(d, 'ja')
    cm = f"{d['cm']:g}"
    ft = d.get('ftin') or ''
    r = H_RANK.get(d.get('variant_of') or d['name'], H_TOTAL)
    if d['stature_basis'] == 'head':
        gap = d['stature_cm'] - ROSTER_AVG
        where = ('少し低めです' if gap < -2 else
                 ('少し高めです' if gap > 2 else 'ほぼ同じです'))
        frame = (f"{n}は公式で{cm}cm（{ft}）ですが、この数字は耳を含みます。"
                 f"頭頂ベースだと約{lnum(d['stature_cm'])}cm（{d['ftin_stature']}）で、"
                 f"ロスター平均より{where}。")
    elif d['height_group'] == 'Tall':
        if r <= 3:
            frame = f"{n}は{cm}cm（{ft}）で、チャートでもトップクラスの高さです。"
        elif r <= 8:
            frame = f"{n}は{cm}cm（{ft}）。{H_TOTAL}人中{r}番目で、かなり背が高いほうです。"
        else:
            frame = f"{n}は{cm}cm（{ft}）。ロスター平均を上回る、{H_TOTAL}人中{r}番目の高さです。"
    elif d['height_group'] == 'Petite':
        frame = f"{n}は{cm}cm（{ft}）と小柄で、チャートでもかなりコンパクトなほうです。"
    else:
        frame = f"{n}は{cm}cm（{ft}）で、ロスター平均とほぼ同じくらいです。"
    bust = f"バストは{lv(d, unit, 'ja', 'bust_in', 'bust_cm')}（UK {d['uk']}）で、{rel_bust_l(d['p_bust_cm'], REL_BUST_JA)}です。"
    waist = (f"ウエストは{lv(d, unit, 'ja', 'waist_in', 'waist_cm')}"
             f"（ウエスト対身長{d['whtr']:.2f}）で、{WAIST_JA[d['waist_level']]}です。")
    if d['thigh_cm'] is not None:
        hips = (f"そこから{HIP_JA[d['hip_level']]}ヒップ（{lv(d, unit, 'ja', 'hip_in', 'hip_cm')}）に、"
                f"{THIGH_JA[d['thigh_level']]}太もも（{lv(d, unit, 'ja', 'thigh_in', 'thigh_cm')}）が続きます。"
                f"太もも周囲は{rank_l(d['p_thigh_cm'], 'ja')}です。")
    else:
        hips = (f"ヒップは{lv(d, unit, 'ja', 'hip_in', 'hip_cm')}で、{HIP_SENT_JA[d['hip_level']]}。"
                f"太ももは信頼できる計測がありません。")
    b, h = d['bust_cm'], d['hip_cm']
    if b > h * 1.10:
        balance = 'バストのほうがやや存在感があります'
    elif h > b * 1.10:
        balance = 'ヒップのほうがやや存在感があります'
    else:
        balance = 'バストとヒップはほぼ均等'
    bw = b / d['waist_cm'] if b and d['waist_cm'] else 0
    hw = h / d['waist_cm'] if h and d['waist_cm'] else 0
    bhi = min(b, h) / max(b, h)
    shape = (f"バスト/ウエスト{bw:.2f}、ヒップ/ウエスト{hw:.2f}、"
             f"バストとヒップのバランスは{bhi*100:.0f}%。全体は{SHAPE_JA[d['shape']]}シルエットで、{balance}です。")
    parts = [frame, bust, waist, hips, shape]
    if compare is None and d.get('variant_of'):
        compare = by_key.get(d['variant_of'])
    if compare is not None:
        if unit == 'cm':
            dB = (d['bust_cm'] or 0) - (compare['bust_cm'] or 0)
            dW = (d['waist_cm'] or 0) - (compare['waist_cm'] or 0)
            dH = (d['hip_cm'] or 0) - (compare['hip_cm'] or 0)
            u = 'cm'
        else:
            dB = (d['bust_in'] or 0) - (compare['bust_in'] or 0)
            dW = (d['waist_in'] or 0) - (compare['waist_in'] or 0)
            dH = (d['hip_in'] or 0) - (compare['hip_in'] or 0)
            u = 'インチ'
        if max(abs(dB), abs(dW), abs(dH)) >= (1.2 if unit == 'cm' else 0.5):
            parts.append(f"標準モデルと比べると、この衣装はバスト{dB:+.1f}{u}、"
                         f"ウエスト{dW:+.1f}{u}、ヒップ{dH:+.1f}{u}。")
    note = note_l(d, 'ja')
    if note:
        parts.append(f"チャート注記：{note}。")
    return ''.join(parts)


def describe_zh(d, unit, compare=None):
    n = lname(d, 'zh')
    cm = f"{d['cm']:g}"
    ft = d.get('ftin') or ''
    r = H_RANK.get(d.get('variant_of') or d['name'], H_TOTAL)
    if d['stature_basis'] == 'head':
        gap = d['stature_cm'] - ROSTER_AVG
        where = ('比全榜平均略低' if gap < -2 else
                 ('比全榜平均略高' if gap > 2 else '和全榜平均差不多'))
        frame = (f"{n}的官方身高是{cm}厘米（{ft}），不过这个数字把耳朵也算进去了。"
                 f"按头顶算大约{lnum(d['stature_cm'])}厘米（{d['ftin_stature']}），{where}。")
    elif d['height_group'] == 'Tall':
        if r <= 3:
            frame = f"{n}身高{cm}厘米（{ft}），在全榜里属于最高的一档。"
        elif r <= 8:
            frame = f"{n}身高{cm}厘米（{ft}），{H_TOTAL}位角色中排第{r}，算是相当高挑。"
        else:
            frame = f"{n}身高{cm}厘米（{ft}），高于全榜平均，在{H_TOTAL}位角色中排第{r}。"
    elif d['height_group'] == 'Petite':
        frame = f"{n}身高{cm}厘米（{ft}），个子很小巧，在全榜里属于最紧凑的一档。"
    else:
        frame = f"{n}身高{cm}厘米（{ft}），和全榜平均差不多。"
    bust = f"胸围{lv(d, unit, 'zh', 'bust_in', 'bust_cm')}（UK {d['uk']}），{rel_bust_l(d['p_bust_cm'], REL_BUST_ZH)}。"
    waist = (f"腰围{lv(d, unit, 'zh', 'waist_in', 'waist_cm')}"
             f"（腰高比{d['whtr']:.2f}），{WAIST_ZH[d['waist_level']]}。")
    if d['thigh_cm'] is not None:
        hips = (f"往下是{HIP_ZH[d['hip_level']]}臀围（{lv(d, unit, 'zh', 'hip_in', 'hip_cm')}），"
                f"配上{THIGH_ZH[d['thigh_level']]}大腿（{lv(d, unit, 'zh', 'thigh_in', 'thigh_cm')}）；"
                f"大腿围{rank_l(d['p_thigh_cm'], 'zh')}。")
    else:
        hips = (f"臀围{lv(d, unit, 'zh', 'hip_in', 'hip_cm')}，{HIP_SENT_ZH[d['hip_level']]}；"
                f"大腿没有可靠数据。")
    b, h = d['bust_cm'], d['hip_cm']
    if b > h * 1.10:
        balance = '胸部更有存在感'
    elif h > b * 1.10:
        balance = '臀部更有存在感'
    else:
        balance = '胸胯比较均衡'
    bw = b / d['waist_cm'] if b and d['waist_cm'] else 0
    hw = h / d['waist_cm'] if h and d['waist_cm'] else 0
    bhi = min(b, h) / max(b, h)
    shape = (f"胸腰比{bw:.2f}、臀腰比{hw:.2f}，胸胯平衡度{bhi*100:.0f}%。"
             f"整体是{SHAPE_ZH[d['shape']]}，{balance}。")
    parts = [frame, bust, waist, hips, shape]
    if compare is None and d.get('variant_of'):
        compare = by_key.get(d['variant_of'])
    if compare is not None:
        if unit == 'cm':
            dB = (d['bust_cm'] or 0) - (compare['bust_cm'] or 0)
            dW = (d['waist_cm'] or 0) - (compare['waist_cm'] or 0)
            dH = (d['hip_cm'] or 0) - (compare['hip_cm'] or 0)
            u = '厘米'
        else:
            dB = (d['bust_in'] or 0) - (compare['bust_in'] or 0)
            dW = (d['waist_in'] or 0) - (compare['waist_in'] or 0)
            dH = (d['hip_in'] or 0) - (compare['hip_in'] or 0)
            u = '英寸'
        if max(abs(dB), abs(dW), abs(dH)) >= (1.2 if unit == 'cm' else 0.5):
            parts.append(f"和标准模型相比，这套服装的胸围{dB:+.1f}{u}、"
                         f"腰围{dW:+.1f}{u}、臀围{dH:+.1f}{u}。")
    note = note_l(d, 'zh')
    if note:
        parts.append(f"榜单注记：{note}。")
    return ''.join(parts)


def read_line_ja(d):
    frame = FRAME_JA[d['height_group']]
    bits = []
    if d['p_bust_cm'] is not None:
        if d['p_bust_cm'] >= 0.7: bits.append('胸はしっかりめ')
        elif d['p_bust_cm'] <= 0.3: bits.append('胸は控えめ')
    if d['p_waist_cm'] is not None:
        if d['p_waist_cm'] >= 0.7: bits.append('ウエストはしっかりめ')
        elif d['p_waist_cm'] <= 0.3: bits.append('ウエストは細め')
    if d['p_hip_cm'] is not None:
        if d['p_hip_cm'] >= 0.7: bits.append('ヒップは広め')
        elif d['p_hip_cm'] <= 0.3: bits.append('ヒップはコンパクト')
    if d['thigh_cm'] is not None and d['p_thigh_cm'] is not None:
        if d['p_thigh_cm'] >= 0.66: bits.append('太ももは太め')
        elif d['p_thigh_cm'] <= 0.33: bits.append('太ももは細め')
    line = frame + 'で'
    if bits:
        line += '、' + '、'.join(bits)
    line += f"。{SHAPE_JA[d['shape']]}シルエットで、{BALANCE_JA[d['balance']]}。"
    return line


def read_line_zh(d):
    frame = FRAME_ZH[d['height_group']]
    bits = []
    if d['p_bust_cm'] is not None:
        if d['p_bust_cm'] >= 0.7: bits.append('胸部偏丰满')
        elif d['p_bust_cm'] <= 0.3: bits.append('胸部偏含蓄')
    if d['p_waist_cm'] is not None:
        if d['p_waist_cm'] >= 0.7: bits.append('腰比较有肉')
        elif d['p_waist_cm'] <= 0.3: bits.append('腰很细')
    if d['p_hip_cm'] is not None:
        if d['p_hip_cm'] >= 0.7: bits.append('胯部较宽')
        elif d['p_hip_cm'] <= 0.3: bits.append('胯部较窄')
    if d['thigh_cm'] is not None and d['p_thigh_cm'] is not None:
        if d['p_thigh_cm'] >= 0.66: bits.append('大腿偏丰满')
        elif d['p_thigh_cm'] <= 0.33: bits.append('大腿偏细')
    line = f"{frame}"
    if bits:
        line += '，' + '，'.join(bits)
    line += f"。整体是{SHAPE_ZH[d['shape']]}轮廓，{BALANCE_ZH[d['balance']]}。"
    return line


def local_tags(d, lang):
    table = TAG_JA if lang == 'ja' else TAG_ZH
    return {k: table.get(v, v) for k, v in build_tags(d).items()}

for d in data:
    d['desc_cm'] = describe(d, 'cm')
    d['desc_in'] = describe(d, 'in')
    d['desc_ja_cm'] = describe_ja(d, 'cm')
    d['desc_ja_in'] = describe_ja(d, 'in')
    d['desc_zh_cm'] = describe_zh(d, 'cm')
    d['desc_zh_in'] = describe_zh(d, 'in')
    d.pop('desc', None)
    d['tags'] = build_tags(d)
    d['tags_ja'] = local_tags(d, 'ja')
    d['tags_zh'] = local_tags(d, 'zh')
    d['read'] = read_line(d)
    d['read_ja'] = read_line_ja(d)
    d['read_zh'] = read_line_zh(d)
    d['notes_ja'] = note_l(d, 'ja')
    d['notes_zh'] = note_l(d, 'zh')
    # an outfit variant keeps its own text and tags; it is always compared
    # against the standard model that owns it
    s = d.get('skin')
    if s:
        s['desc_cm'] = describe(s, 'cm', compare=d)
        s['desc_in'] = describe(s, 'in', compare=d)
        s['desc_ja_cm'] = describe_ja(s, 'cm', compare=d)
        s['desc_ja_in'] = describe_ja(s, 'in', compare=d)
        s['desc_zh_cm'] = describe_zh(s, 'cm', compare=d)
        s['desc_zh_in'] = describe_zh(s, 'in', compare=d)
        s.pop('desc', None)
        s['tags'] = build_tags(s)
        s['tags_ja'] = local_tags(s, 'ja')
        s['tags_zh'] = local_tags(s, 'zh')
        s['read'] = read_line(s)
        s['read_ja'] = read_line_ja(s)
        s['read_zh'] = read_line_zh(s)
        s['notes_ja'] = note_l(s, 'ja')
        s['notes_zh'] = note_l(s, 'zh')

json.dump(data, open(ROOT/'tools/data.json','w'), indent=1, ensure_ascii=False)
print('descriptions written (cm + in)\n')
samples = data[:2] + [by_key['Rina']]
for d in data:
    if d.get('skin'):
        samples.append(d['skin'])
        break
for d in samples:
    print('*', d['display'], '· CM:')
    print(' ', d['desc_cm'])
    print(' · IN:')
    print(' ', d['desc_in'])
    print()
