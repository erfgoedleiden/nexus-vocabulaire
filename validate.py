import os
from urllib.error import HTTPError
from urllib.request import urlopen

import pyshacl
import rdflib


def main() -> int:
    shacl_validate()
    check_links()

    return 0


def shacl_validate():
    """
    Validates the data samples against the data shape constraint definitions

    :return: None
    """
    data_samples = os.listdir('voorbeelddata')
    for sample_file in data_samples:
        camel_cased = ''.join([name.capitalize() for name in sample_file.split('_')])

        conforms, results_graph, results_text = pyshacl.validate(
            data_graph=os.path.join('voorbeelddata', sample_file),
            shacl_graph=os.path.join('shacl', camel_cased),
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
                    # TODO: parse response from URI to match hash uris against subjects in the graph in order to
                    #  validate

                    # urlopen will throw an error on 400 or larger responses
                    try:
                        urlopen(triple_part).read()
                    except HTTPError as e:
                        print(f'{triple_part} could not be resolved: {e}')
                        raise


if __name__ == '__main__':
    raise SystemExit(main())