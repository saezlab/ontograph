# Welcome to OntoGraph

![Image title](assets/project-banner-readme.png){ align=center }

**OntoGraph** is a Python package for programmatic access, navigation, and analysis of biomedical ontologies. It provides a unified interface to download, load, and query ontologies from the [OBO Foundry](https://obofoundry.org/) and other sources, supporting both OBO and OWL formats.

---

## Key Features

- **Ontology Catalog Access**  
  Browse and retrieve metadata for hundreds of ontologies from the OBO Foundry registry.

- **Flexible Ontology Loading**  
  Load ontologies from local files, remote URLs, or directly from the OBO Foundry catalog.

- **Graph Navigation & Querying**  
  Traverse ontology graphs: get parents, children, ancestors, descendants, siblings, and roots of terms.

- **Relationship Analysis**  
  Check ancestor/descendant/sibling relationships, find common and lowest common ancestors, and compute distances between terms.

- **Introspection Utilities**  
  Analyze ontology structure, calculate paths and trajectories, and visualize term hierarchies.

- **Caching & Download Management**  
  Efficiently download and cache ontology files for offline use.

---

## Main Components

- **ClientCatalog**  
  Interact with the ontology catalog: list available ontologies, retrieve metadata, and explore catalog structure.

- **ClientOntology**  
  Load and query individual ontologies: navigate term relationships, analyze graph structure, and perform advanced queries.

- **Loader & Downloader Modules**  
  Abstract and concrete classes for loading ontologies and managing downloads from various sources.

- **Query Adapters**  
  Modular classes for navigation (`OntologyNavigator`), relationship analysis (`OntologyRelations`), and introspection (`OntologyIntrospection`).

---

## Why OntoGraph?

- Unified and extensible API for ontology operations
- Designed for both interactive exploration and programmatic workflows
- Built-in support for caching and efficient data management
- Modular architecture for easy integration and extension

---

> _Explore, analyze, and integrate ontologies with ease using OntoGraph!_

---
