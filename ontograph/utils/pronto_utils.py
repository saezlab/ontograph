

def extract_terms(ontology, include_obsolete=False):
    """Single-pass extraction of pronto.Term objects, sorted by term.id."""
    terms = [t for t in ontology.terms() if include_obsolete or not t.obsolete]
    terms.sort(key=lambda t: t.id)
    return terms