![project-banner](./docs/assets/project-banner-readme.png)

# OntoGraph Package

[![Unit Tests](https://img.shields.io/github/actions/workflow/status/saezlab/ontograph/ci-testing-unit.yml?branch=master)](https://github.com/saezlab/ontograph/actions/workflows/ci-testing-unit.yml)
[![Docs](https://img.shields.io/badge/docs-MkDocs-blue)](https://saezlab.github.io/ontograph/)
![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![PyPI](https://img.shields.io/pypi/v/ontograph)
![Python](https://img.shields.io/pypi/pyversions/ontograph)
![License](https://img.shields.io/github/license/saezlab/ontograph)
![Issues](https://img.shields.io/github/issues/saezlab/ontograph)
![Last Commit](https://img.shields.io/github/last-commit/saezlab/ontograph)

## Description

A lightweight Python package for loading, representing, and efficiently querying biological ontologies as graph structures.

## Installation

This package is under development, by this time you can clone the repository and install the package in "editable" (`-e` or `--editable`) mode

```bash
git clone https://github.com/saezlab/ontograph.git
uv pip install -e .
```

## Usage

### Interacting locally with the OBO Foundry catalog

```python
from ontograph.client import ClientCatalog

# Instantiate a client for your catalog
client_catalog = ClientCatalog(cache_dir="./data/out")

# Load the catalog, in case this one doesn't exist it will be downloaded automatically in the cache folder you specify.
client_catalog.load_catalog()
```

#### Retrieve the list of ontologies (name_id and description) in OBO Foundries 
```bash
ontologies_list = client_catalog.list_available_ontologies()
```

#### Print the list in a suitable format
```bash
client_catalog.print_available_ontologies()
```
#### Obtain metadata about an specific ontology
```bash
metadata_go = client_catalog.get_ontology_metadata(ontology_id="go", show_metadata=True) # Print in terminal
```

### Interacting with an ontology
#### Create a client for your ontology
```python
from ontograph.client import ClientOntology

# Instantiate a client for your ontology
client_dummy_ontology = ClientOntology(cache_dir="./data/out")

# Load a dummy ontology, we prepare a simple one to try out this package.
client_dummy_ontology.load(file_path_ontology="./tests/resources/dummy_ontology.obo")
```
#### Queries for your ontology

We included a demo file containing the following graph representing an ontology. The Node "Z" represents the Root node of this ontology.

```mermaid
graph TB
    
    Z((Z)) --> A((A))
    Z((Z)) --> B((B))
    Z((Z)) --> C((C))

    A((A)) --> D((D))
    B((B)) --> H((H))
    B((B)) --> I((I))
    C((C)) --> J((J))

    D((D)) --> E((E))
    D((D)) --> F((F))
    D((D)) --> G((G))
    H((H)) --> K((K))
    I((I)) --> L((L))
    J((J)) --> M((M))

    E((E)) --> N((N))
    F((F)) --> O((O))
    F((F)) --> Y((Y))
    G((G)) --> K1((K1))
    G((G)) --> K2((K2))
    K((K)) --> Q((Q))
    K((K)) --> G1((G))
    M((M)) --> S((S))

    G1((G)) --> K11((K1))
    G1((G)) --> K21((K2))
    S((S)) --> T((T))

    T((T)) --> U((U))
    
    U((T)) --> V((V))
    U((U)) --> W((W))
    
    W((W)) --> Y1((Y))


```

##### Navigation
- `client_dummy_ontology.get_ancestors(term_id="S")`
- `list(client_dummy_ontology.get_ancestors_with_distance(term_id="S"))`
- `client_dummy_ontology.get_children(term_id="A")`
- `client_dummy_ontology.get_descendants(term_id="U")`
- `list(client_dummy_ontology.get_descendants_with_distance(term_id="U"))`
- `client_dummy_ontology.get_parents(term_id="U")`
- `client_dummy_ontology.get_root()`
- `client_dummy_ontology.get_siblings(term_id="K1")`
- `client_dummy_ontology.get_term(term_id="E")`

##### Relations
- `client_dummy_ontology.get_common_ancestors(node_ids=["K", "L"])`
- `client_dummy_ontology.get_lowest_common_ancestors(node_ids=["K", "L"])`
- `client_dummy_ontology.is_ancestor(ancestor_node="A", descendant_node="N")`
- `client_dummy_ontology.is_descendant(descendant_node="A", ancestor_node="N")`
- `client_dummy_ontology.is_sibling(nodeA="F", nodeB="G")`

##### Introspection
- `client_dummy_ontology.get_distance_from_root(term_id="V")`
- `client_dummy_ontology.get_path_between(nodeA="Q", nodeB="B")`
- `trajectories = client_dummy_ontology.get_trajectories_from_root(term_id="Y")`
- `client_dummy_ontology.print_term_trajectories_tree(trajectories)`

## Further steps
If you are interested in loading an ontology from the catalog, just use the `name_id` and `format` of that specific ontology. For instance, `name_id="go"` and `format="obo"`.

```bash
client_go = ClientOntology()
client_go.load(name_id="go", format="obo")
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

- Community Standards and Code of Conduct
    - We value a respectful, inclusive, and collaborative environment. Please read our [Code of Conduct](./CODE_OF_CONDUCT.md) before participating (issues, discussions, PRs).
    - For contribution guidelines (how to propose changes, style, testing), see the [Community docs](./docs/community/).

### Choosing a Pull Request template

When opening a PR, GitHub will offer a template picker:
- Use the default template for most changes.
- Choose a specialized template under `.github/PULL_REQUEST_TEMPLATE/` when appropriate:
    - `bug_fix.md` — reported issues and regressions
    - `feature.md` — new capabilities or enhancements
    - `docs.md` — documentation-only updates
    - `maintenance.md` — tooling, CI, dependencies, formatting
    - `performance.md` — optimizations with benchmarks
    - `breaking_change.md` — changes that require migration guidance

Each template includes a checklist for tests, docs, pre-commit, and changelog entries.

## License

[MIT](https://choosealicense.com/licenses/mit/)
