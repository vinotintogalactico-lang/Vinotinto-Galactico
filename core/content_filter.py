def is_valid_content(title: str, category: str, body: str = "") -> bool:
    """
    Verifica si una noticia debe ser incluida en base a palabras clave en su título o en su cuerpo.
    """
    t = title.lower()
    b = body.lower()

    # ── REGLAS GLOBALES ──────────────────────────────────────────────────────
    if not t:
        return False

    # Combinar título y cuerpo para escaneo profundo
    full_text = t + " " + b

    # ── REGLAS POR CATEGORÍA ─────────────────────────────────────────────────

    if category == "Mundial Global":
        # Enfoque PERMISIVO: dejamos pasar cualquier noticia deportiva de fútbol.
        # Solo bloqueamos lo que claramente NO es fútbol internacional del Mundial.
        forbidden = [
            "nba", "fórmula 1", "formula 1", "tenis", "golf", "ciclismo",
            "baloncesto", "basket", "moto gp", "boxeo", "ufc", "béisbol",
            "premier league", "champions league", "laliga", "bundesliga",
            "serie a", "liga f", "eurocopa", "copa del rey",
            "fichaje", "traspaso", "mercado de pases", "cláusula de rescisión"
        ]
        if any(f in full_text for f in forbidden):
            return False
        # No se exige must_have: cualquier noticia que no esté prohibida pasa.

    elif category == "Real Madrid Masculino":
        exclusiones = [
            "femenino", "femenina", "castilla", "baloncesto", "basket", "sub-20", "sub 20", "juvenil",
            "liga f", "primera iberdrola", "champions femenina", "jugadora", "jugadoras"
        ]
        if any(x in full_text for x in exclusiones):
            return False

    elif category == "Real Madrid Femenino":
        if any(x in full_text for x in ["masculino", "castilla", "baloncesto", "basket"]):
            return False
        otros_equipos = ["atletico", "atlético", "barcelona", "chelsea", "lyon",
                         "wolfsburg", "arsenal", "psg", "manchester", "juventus",
                         "sevilla", "levante", "valencia", "sporting", "betis"]
        if any(eq in t for eq in otros_equipos):
            rm_refs = ["real madrid", "madrid femenino", "blancas", "liga f", "primera iberdrola"]
            if not any(ref in full_text for ref in rm_refs):
                return False
        must_have = [
            "real madrid", "madrid femenino", "blancas",
            "primera iberdrola", "liga f", "jugadora", "femenino", "femenina"
        ]
        if not any(m in full_text for m in must_have):
            return False

    elif category == "Selección Española Masculina":
        if any(x in t for x in ["femenina", "femenino"]):
            return False

    elif category == "Selección Española Femenina":
        if any(x in t for x in ["masculino", "masculina"]):
            return False
        direct_spain = [
            "selección española", "seleccion española",
            "selección femenina", "seleccion femenina",
            "la roja", "montse tomé", "montse tome",
            "españa", "española", "mundial", "eurocopa"
        ]
        if not any(d in t for d in direct_spain):
            return False
        if any(c in t for c in ["barcelona", "barça", "blaugrana", "atletico", "atlético"]) and not any(s in t for s in ["selección", "seleccion", "españa", "la roja"]):
            return False
        otros_paises = ["islandia", "alemania", "francia", "england", "netherlands",
                        "holanda", "suecia", "noruega", "italia", "portugal",
                        "estados unidos", "brasil", "argentina", "colombia"]
        if any(p in t for p in otros_paises):
            if not any(d in t for d in direct_spain):
                return False

    elif category == "Vinotinto Masculina":
        if any(x in t for x in ["femenina", "femenino", "chicas", "mujeres", "sub-20", "sub 20", "sub-17", "sub 17"]):
            return False
        must_have = [
            "vinotinto", "venezuela", "venezolano", "venezolana",
            "batista", "rondón", "rondon", "soteldo", "aramburu",
            "machís", "machis", "yangel herrera", "savarino", "bello",
            "ferraresi", "osorio", "peñaranda", "penaranda"
        ]
        if not any(m in t for m in must_have):
            return False

    elif category == "Vinotinto Femenina":
        if any(x in t for x in ["masculino", "hombres"]):
            return False
        must_have = ["vinotinto", "venezuela", "venezolana"]
        if not any(m in t for m in must_have):
            return False

    elif category in ["LaLiga", "Fútbol Nacional"]:
        if any(x in t for x in ["femenino", "femenina"]):
            return False
        if any(x in t for x in ["nba", "tenis", "formula 1", "moto gp", "baloncesto",
                                  "champions league", "premier", "bundesliga", "serie a"]):
            return False

    return True
