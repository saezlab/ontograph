from pronto import Ontology


def extract_terms(ontology: Ontology, include_obsolete: bool = False) -> list:
    """Single-pass extraction of pronto.Term objects, sorted by term.id."""
    terms = [t for t in ontology.terms() if include_obsolete or not t.obsolete]
    terms.sort(key=lambda t: t.id)
    return terms
