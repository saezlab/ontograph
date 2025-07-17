from dataclasses import dataclass
from pronto import Ontology

# Import the logic to deal with OBO Foundry registry (Implementation)
from ontology_registry import OBORegistryAdapter

# Import the logic to download files (Implementation)
from downloader import PoochDownloaderAdapter

# Import the logic to load ontologies (Implementation)
from ontology_loader import ProntoLoaderAdapter


cache_dir = "../data/out"

ontologies_registry = OBORegistryAdapter(cache_dir=cache_dir)

downloader = PoochDownloaderAdapter(cache_dir=cache_dir, registry=ontologies_registry)


class Ontology:
    def __init__(self):
        pass


class Registry:
    def __init__(self):
        pass


class Client:
    def __init__(self):
        self.__registry  # This one needs to be instantiated Just one time (singleton?)
        self.__ontology  # This one can be instantiated multiple times

    # methods for manipulating the registry
    def __initialize_registry():
        pass

    # methods for manipulating the ontology
    def __initialize_ontology():
        pass


# 1.
"""

import ontograph as op


onto_registry = op.registry() 

onto_registry.list_ontologies()

onto_registry.load_registry()

onto_registry.registry()

onto_registry.list_available_ontologies()

onto_registry.print_registry_schema_tree()

onto_registry.get_ontology_metadata()

onto_registry.get_download_url()

onto_registry.get_available_formats()



# Similar to Pandas Dataframe Look & Feel
go = op.load(path: str, name_id: str, format: str = "obo")

go.get_parents(term_id: str, depth: int = -1, include_self: bool = False)

go.get_children(term_id: str, depth: int = -1, include_self: bool = False)

go.get_siblings(term_id)

go.get_roots()

go.get_leaves()

go.find_path(source_id, target_id)

go.is_descendant(child_id, parent_id)

go.get_depth(term_id)

go.list_terms(prefix="GO:", include_obsolete=False)

go.get_term_info(term_id)

go.search_terms(query="metabolic process", exact=False)

go.get_relationships(term_id)

go.get_terms_by_relation(terms="part_of")

go.get_common_ancestors(term_ids)

go.term_exists(term_id)


"""
