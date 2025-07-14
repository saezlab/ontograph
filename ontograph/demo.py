from pathlib import Path

from ontograph.ontology_registry import OBORegistryAdapter
from ontograph.downloader import PoochDownloaderAdapter
from ontograph.ontology_loader import ProntoLoaderAdapter
from ontograph.ontology_query import OntologyQueries


if __name__ == "__main__":

    cache_dir = Path("./data/out")

    # ----------------------------------------------------
    # Step 1. Create a registry with all the ontologies
    # ----------------------------------------------------
    onto_registry = OBORegistryAdapter(cache_dir=cache_dir)

    # Load the registry (in case of not having the registry it will be downloaded automatically)
    onto_registry.load_registry()

    # Print registry' schema
    onto_registry.print_registry_schema_tree()

    # List of available ontologies
    print("Number of ontologies: {}".format(onto_registry.list_available_ontologies()))

    # Print the link associated to a valid ontology (e.g., 'chebi')
    print(onto_registry.get_download_url("chebi", "obo"))

    # Print available formats for a valid ontology
    print(onto_registry.get_available_formats(ontology_id="chebi"))

    # ----------------------------------------------------
    # Step 2. Download specific ontologies
    # ----------------------------------------------------
    downloader = PoochDownloaderAdapter(cache_dir=cache_dir, registry=onto_registry)

    resources = [
        {"name_id": "chebi", "format": "owl"},
        {"name_id": "go", "format": "obo"},
        {"name_id": "ado", "format": "owl"},
    ]
    batch_results = downloader.fetch_batch(resources)
    print("Batch download results:", batch_results)

    # ----------------------------------------------------
    # Step 3. Load ontologies
    # ----------------------------------------------------
    ontology_loader = ProntoLoaderAdapter(cache_dir=cache_dir)

    # Ontology "go"
    name_id_go = "go"
    format_go = "obo"

    gene_ontology = ontology_loader.load(name_id=name_id_go, format=format_go)
    print(f"Loaded ontology: {name_id_go}.{format_go}")
    print(f"Number of terms: {len(gene_ontology.terms())}")

    # term_id = "GO:0008150" # biological_process
    # term_id = "GO:0160266"  # anestrus phase
    term_id = "GO:0070360"  # symbiont-mediated actin polymerization-dependent cell-to-cell migration in host

    queries = OntologyQueries(gene_ontology)

    # Print term relations
    print(f"Term: {term_id}")
    print(f"  Parents     : {queries.parents(term_id)}")
    print(f"  Children    : {queries.children(term_id)}")
    # print(f"  Ancestors   : {queries.ancestors(term_id)}")
    # print(f"  Descendants : {queries.descendants(term_id)}")
