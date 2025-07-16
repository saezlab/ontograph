# API final view from user perspective

## Importing the library
- Complete import of Ontograph
```python
import ontograph
```   


## Download Ontologies
- Download a single ontology from standard resources
```python
resource = [
    {"name_id": "go", "format": "obo"},
]

path_ontologie = ontograph.downloader.download(resource, cache_directory)
```   

- Download a multiple ontologies from standard resources
```python
resources = [
    {"name_id": "go", "format": "obo"},
    {"name_id": "chebi", "format": "owl"},
]

paths_ontologies = ontograph.downloader.download(resources, cache_directory)
```

## Load ontologies

- Load the "ontology from standard resources, or local source"
```python
gene_ontology = ontograph.load(name_id="go", format="obo")
```

## Exploring the ontology

- Print the metadata related to the ontology
```python
gene_ontology.metadata()
```

- Print the roots of the ontology
```python
gene_ontology.roots()
```


```mermaid
flowchart TD
    %% API Layer
    A1[OntologyClient<br>api/client.py]

    %% Core Domain
    subgraph Core
        B1[OntologyGraph<br>core/ontology_graph.py]
        B2[QueryEngine<br>core/query_engine.py]
        B3[TermMapping<br>core/term_mapping.py]
    end

    %% Ports (Interfaces)
    subgraph Ports
        P1[OntologyLoader<br>ports/ontology_loader.py]
        P2[GraphBackend<br>ports/graph_backend.py]
        P3[Downloader<br>ports/downloader.py]
    end

    %% Adapters
    subgraph Adapters
        C1[pronto_loader.py]
        C2[pronto_graph.py]
        C3[pooch_downloader.py]
        C4[tsv_mapping_loader.py]
    end

    %% Utilities & Config (internal use only)
    subgraph Utils_Config
        U1[file_cache.py]
        U2[validation.py]
        U3[logging.py]
        S1[settings.py]
    end

    %% Connections
    A1 --> B1
    A1 --> B2
    A1 --> B3

    %% Core uses Ports (interfaces)
    B1 --> P1
    B2 --> P2
    B3 --> P3

    %% Adapters implement Ports (interfaces)
    P1 -.-> C1
    P2 -.-> C2
    P3 -.-> C3
    P3 -.-> C4

    %% Internal usage (no direct arrow from API)
    Core --> Utils_Config
    Adapters --> Utils_Config
```

**Legend:**

- --> means "uses"
- -.-> means "implemented by"
