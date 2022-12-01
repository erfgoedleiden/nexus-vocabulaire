import os
from urllib.error import HTTPError
from urllib.request import urlopen

import pyshacl
import rdflib


def main() -> int:
    check_links()
    shacl_validate()

    return 0


def shacl_validate():
    """
    Validates the data samples against the data shape constraint definitions

    :return: None
    """
    data_samples = os.listdir('voorbeelddata')
    for sample_file in data_samples:
        conforms, results_graph, results_text = pyshacl.validate(
            data_graph=os.path.join('voorbeelddata', sample_file),
            shacl_graph=os.path.join('shacl', sample_file),
        )
        assert conforms, f'{sample_file} incorrect: {results_text}'


def check_links() -> None:
    """
    This function will check _every_ URI in the sample graphs for being able to resolve. This will catch errors on
    vocab typos, or small happy accidents on hash/slash-URI mishaps and the likes.

    :return: None
    """
    data_samples = os.listdir('voorbeelddata')

    for sample_file in data_samples:
        graph = rdflib.Graph()
        graph.parse(os.path.join('voorbeelddata', sample_file))

        for triple in graph:
            for triple_part in triple:
                if isinstance(triple_part, rdflib.URIRef):
                    # urlopen will throw an error on 400 or larger responses
                    try:
                        urlopen(triple_part).read()
                    except HTTPError as e:
                        f'{triple_part} could not be resolved: {e}'
                        raise


if __name__ == '__main__':
    raise SystemExit(main())