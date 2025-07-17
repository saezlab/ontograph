from dataclasses import dataclass
from typing import Any

from pronto import Ontology

import ontology_registry


__all__ = [
    "OntologyClient",
]


# TODO: create a client interface class to ontograph
@dataclass
class OntologyClient:
    ontology_object: Ontology

    # 1. list of catalog of ontologies
    # TODO: Implement a funtion that returns all the ontologies in the catalog (OBO Foundries)
    def list_ontologies():
        pass

    # 2. load an ontology
    # TODO: Implement a function to load a specified ontology in a given format.
    # This function should accept a target path to download the ontology or retrieve
    # it from cache if already available.
    def load(path: str, name_id: str, format: str = "obo") -> Any:
        pass

    # ----------------------------------------------
    # ----      Core hierarchical queries       ----
    # ----------------------------------------------
    # 3. get parents/ancestors
    # TODO: Implement a function to return all parent terms of a given ontology term,
    # allowing control over the traversal depth.
    def get_parents(
        term_id: str, depth: int = -1, include_self: bool = False
    ) -> list[str]:
        pass

    # 4. get children/descendants
    # TODO: Implement a function to retrieve all child terms of a given ontology term,
    # with optional control over traversal depth.
    def get_children(
        term_id: str, depth: int = -1, include_self: bool = False
    ) -> list[str]:
        pass

    # 5. get siblings
    # TODO: retrieve term sharing the same parents(s)
    def get_siblings(term_id):
        pass

    # 6. get root terms
    # TODO: Retrieve all terms without parents (top categories in our ontology)
    def get_roots():
        pass

    # 7. get leaf terms
    # TODO: retrieve all terms without children (e.g., most specific categories)
    def get_leaves():
        pass

    # ----------------------------------------------
    # ----        Graph & Path queries          ----
    # ----------------------------------------------
    # 8. find path between two terms
    # TODO: determine the relationship?path between two terms (if any)
    def find_path(source_id, target_id):
        pass

    # 9. Check subsumption (is a relationship)
    # TODO: Check if a term is descendant of another
    def is_descendant(child_id, parent_id):
        pass

    # 10. get_depth(term_id)
    # TODO: return the depth of a term in the hierarchy
    def get_depth(term_id):
        pass

    # ----------------------------------------------
    # ----      Ontology Metadata queries       ----
    # ----------------------------------------------
    # 11. List of terms
    # TODO: Enumerate all terms with optional filtering
    # TODO: clarify function
    def list_terms(prefix="GO:", include_obsolete=False):
        pass

    # 12. get term metadata
    # TODO: retrieve details such as label, definition, synonyms, etc.
    def get_term_info(term_id):
        pass

    # 12. Search terms by label or synonym
    # TODO: Fuzzy or exact search for term labels.
    # TODO: clarify this function
    def search_terms(query="metabolic process", exact=False):
        pass

    # ----------------------------------------------
    # ----      Advanced semantic  queries      ----
    # ----------------------------------------------
    # 13. get relationships of a term
    # TODO: Return all relationships (not just hierarchical: part_of, regulates, etc.).
    # TODO: clarify
    def get_relationships(term_id):
        pass

    # 14. Get terms by relationship type
    # TODO: Retrieve all terms linked via a specific relationship type.
    def get_terms_by_relation(terms="part_of"):
        pass

    # 15. Find common ancestors
    # TODO: Determine shared parent terms between two or more terms.
    def get_common_ancestors(term_ids):
        pass

    # ----------------------------------------------
    # ----              Utilities               ----
    # ----------------------------------------------
    # 16. Check if term exists
    # TODO: Validate a term ID
    def term_exists(term_id):
        pass
