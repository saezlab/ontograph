# Example improved client usage
from ontograph.api.client import OntologyClient

# Initialize client
client = OntologyClient()

# List available ontologies
ontologies = client.list_ontologies()

# Download and load in one step
go = client.load("go", format="obo")

# Query operations
parents = go.get_parents("GO:0008150")
children = go.get_children("GO:0008150")

# Advanced query
results = go.query("ancestors:GO:0008150")
