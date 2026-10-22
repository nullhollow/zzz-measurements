"""Complete, localized measurement summaries for search and structured data."""


def profile_summary(d, lang='en'):
    name = d.get(f'name_{lang}') or d['display']
    height, bust, waist, hip = (f'{d[k]:g}' for k in
                               ('stature_cm', 'bust_cm', 'waist_cm', 'hip_cm'))
    shape = (d.get(f'tags_{lang}') or d['tags'])['shape']
    if lang == 'ja':
        return (f"{name}の寸法は身長{height}cm、バスト{bust}cm、"
                f"ウエスト{waist}cm、ヒップ{hip}cm。UK {d['uk']}、{shape}のシルエット。")
    if lang == 'zh':
        return (f"{name}身高{height}厘米，胸围{bust}厘米、腰围{waist}厘米、"
                f"臀围{hip}厘米。UK {d['uk']}，{shape}轮廓。")
    return (f"{name}: height {height} cm, bust {bust} cm, waist {waist} cm, "
            f"hips {hip} cm; UK {d['uk']}. {shape} silhouette.")
