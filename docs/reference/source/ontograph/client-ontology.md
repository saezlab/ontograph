# ClientOntology

`ClientOntology` is the main interface for loading, navigating, and querying individual ontologies in OntoGraph.  
It allows you to load ontologies from local files, the OBO Foundry catalog, or remote URLs, and provides a unified API for exploring ontology terms, relationships, and structure.

This class is ideal for users who want to work directly with a specific ontology—navigating its graph, analyzing relationships, and performing introspection tasks.

---

## Features

- Load ontologies from file, catalog, or URL
- Navigate ontology graphs: get parents, children, ancestors, descendants, siblings, and roots of terms
- Analyze relationships: check ancestor/descendant/sibling status, find common and lowest common ancestors, compute distances
- Introspect ontology structure: calculate paths, trajectories, and visualize term hierarchies
- Modular query adapters for navigation, relations, and introspection

---

## API Reference

::: ontograph.client.ClientOntology

---

## See Also

- [ClientCatalog](client-catalog.md): For exploring and retrieving metadata from the ontology
