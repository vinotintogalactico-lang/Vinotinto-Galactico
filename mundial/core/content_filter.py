"""
Filtro de contenido para el extractor Mundial 2026.

Lógica:
  - Como todos los links ya apuntan a secciones de Mundial o fútbol internacional,
    el filtro es permisivo hacia el fútbol pero bloquea contenido claramente
    fuera de tema (baloncesto, tenis, F1, etc.) y noticias de ligas locales
    que no tengan relación con el Mundial.
"""


def is_valid_content(title: str, category: str, body: str = "") -> bool:
    if not title:
        return False

    t = title.lower()
    b = body.lower()
    full = t + " " + b

    # ── EXCLUSIONES GLOBALES (cualquier categoría) ────────────────────────────
    # Deportes ajenos
    off_topic = [
        "nba", "nfl", "nhl", "mlb", "baloncesto", "basket", "basketball",
        "tenis", "tennis", "fórmula 1", "formula 1", "f1", "motogp", "moto gp",
        "béisbol", "beisbol", "softbol", "golf", "natación", "atletismo",
        "boxeo", "mma", "ufc", "ciclismo", "volleyball", "voleibol",
    ]
    if any(x in t for x in off_topic):
        return False

    # Ligas locales que no sean el Mundial (solo si NO mencionan Mundial)
    local_only = [
        "premier league", "serie a", "bundesliga", "ligue 1",
        "liga mx", "apertura", "clausura", "liga futve", "futve",
        "champions league", "europa league", "conference league",
        "copa del rey", "fa cup", "coppa italia",
    ]
    mundial_refs = [
        "mundial", "world cup", "copa del mundo", "fifa 2026",
        "selección", "seleccion", "national", "eliminatoria",
    ]
    if any(x in full for x in local_only):
        if not any(m in full for m in mundial_refs):
            return False

    # ── CATEGORÍA TV / CANAL ─────────────────────────────────────────────────
    if category == "📺 TV / Canal":
        # Muy permisivo: los canales cubren el Mundial íntegro
        return True

    # ── CATEGORÍA PRENSA ESCRITA ──────────────────────────────────────────────
    elif category == "📰 Prensa Escrita":
        # Permisivo con fútbol internacional / mundial
        return True

    # ── CATEGORÍA DIGITAL ────────────────────────────────────────────────────
    elif category == "💻 Digital":
        return True

    return True
