def is_valid_content(title: str, category: str) -> bool:
    """
    Evalúa si el título de una noticia es pertinente para la categoría solicitada.
    Reglas de exclusión + reglas de inclusión obligatoria (must_have).
    """
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
        # Se quiere un enfoque global, sin preferencias, salvo Portugal ("el bicho")
        # Se incluyen también los principales países/selecciones que participan
        paises = [
            "argentina", "brasil", "colombia", "uruguay", "ecuador", "chile", "peru", "venezuela", "bolivia", "paraguay",
            "méxico", "mexico", "estados unidos", "usa", "canadá", "canada", "costa rica", "panamá", "honduras",
            "españa", "portugal", "francia", "inglaterra", "alemania", "italia", "países bajos", "holanda", "croacia", "bélgica",
            "marruecos", "senegal", "japón", "japon", "corea", "arabia"
        ]
        must_have = ["mundial", "fifa", "copa del mundo", "world cup", "sede", "estadio", "organización", 
                     "selección", "seleccion", "cristiano", "ronaldo", "bicho", "cr7"] + paises
        forbidden = ["fichaje", "mercado", "champions", "traspaso", "premier", "laliga", "nba", "fórmula 1"]
        if any(f in full_text for f in forbidden): return False
        if not any(m in full_text for m in must_have): return False

    elif category == "Real Madrid Masculino":
        # Exclusiones explícitas (Femenino, Cantera y Baloncesto)
        # Se escanea TODO el texto (título y cuerpo) buscando palabras que delaten
        # que es una noticia de fútbol femenino o de otra rama.
        exclusiones = [
            "femenino", "femenina", "castilla", "baloncesto", "basket", "sub-20", "sub 20", "juvenil",
            "liga f", "primera iberdrola", "champions femenina", "jugadora", "jugadoras"
        ]
        if any(x in full_text for x in exclusiones):
            return False
        # Dejamos pasar todo lo demás sin exigir nombres propios.

    elif category == "Real Madrid Femenino":
        # Exclusiones explícitas
        if any(x in full_text for x in ["masculino", "castilla", "baloncesto", "basket"]):
            return False
            
        # Rechazar si menciona OTRO equipo sin mencionar Real Madrid
        otros_equipos = ["atletico", "atlético", "barcelona", "chelsea", "lyon",
                         "wolfsburg", "arsenal", "psg", "manchester", "juventus",
                         "sevilla", "levante", "valencia", "sporting", "betis"]
        if any(eq in t for eq in otros_equipos):
            rm_refs = ["real madrid", "madrid femenino", "blancas", "liga f", "primera iberdrola"]
            if not any(ref in full_text for ref in rm_refs):
                return False
                
        # Asegurar que al menos el contexto del Real Madrid o del fútbol femenino español esté presente
        must_have = [
            "real madrid", "madrid femenino", "blancas",
            "primera iberdrola", "liga f", "jugadora", "femenino", "femenina"
        ]
        if not any(m in full_text for m in must_have):
            return False

    elif category == "Selección Española Masculina":
        if any(x in t for x in ["femenina", "femenino"]):
            return False
        # COMO LOS LINKS YA SON DIRECTOS A LA SECCIÓN, DEJAMOS PASAR TODO LO QUE NO SEA FEMENINO

    elif category == "Selección Española Femenina":
        if any(x in t for x in ["masculino", "masculina"]):
            return False
        # Debe ser estrictamente de la SELECCIÓN, no de clubes como el Barcelona.
        # Si habla de Alexia o Aitana pero en contexto de clubes, se rechaza.
        direct_spain = [
            "selección española", "seleccion española",
            "selección femenina", "seleccion femenina",
            "la roja", "montse tomé", "montse tome",
            "españa", "española", "mundial", "eurocopa"
        ]
        if not any(d in t for d in direct_spain):
            return False
        # Si menciona al Barcelona u otro club sin la selección, fuera.
        if any(c in t for c in ["barcelona", "barça", "blaugrana", "atletico", "atlético"]) and not any(s in t for s in ["selección", "seleccion", "españa", "la roja"]):
            return False
        # Además rechazar si es claramente de otro país/competición sin España
        otros_paises = ["islandia", "alemania", "francia", "england", "netherlands",
                        "holanda", "suecia", "noruega", "italia", "portugal",
                        "estados unidos", "brasil", "argentina", "colombia"]
        if any(p in t for p in otros_paises):
            # Solo pasa si TAMBIÉN menciona España o la selección
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
        # DEBE hablar de la selección de Venezuela, no solo de Deyna en su club.
        must_have = [
            "vinotinto", "venezuela", "venezolana"
        ]
        if not any(m in t for m in must_have):
            return False

    elif category in ["LaLiga", "Fútbol Nacional"]:
        if any(x in t for x in ["femenino", "femenina"]):
            return False
        # No demasiado restrictivo, LaLiga cubre todo el campeonato
        # Solo excluir contenido claramente ajeno
        if any(x in t for x in ["nba", "tenis", "formula 1", "moto gp", "baloncesto",
                                 "champions league", "premier", "bundesliga", "serie a"]):
            return False

    return True
