import pronto


class Ontology:
    def __init__(self, file_path_ontology):
        self.ontology = pronto.Ontology(file_path_ontology)

    def extract_all_subsets(self) -> set:
        # Already efficient
        return {
            subset for term in self.ontology.terms() for subset in term.subsets
        }

    def relationships(self):
        for r in self.ontology.relationships():
            print(r)


def main():
    file_path_ontology = '../data/out/go.obo'
    go = Ontology(file_path_ontology=file_path_ontology)
    print(go.extract_all_subsets())
    print(go.relationships())


if __name__ == '__main__':
    # cProfile.run("main()", filename="profile.prof")
    main()
