import datetime
import logging
import os
from argparse import ArgumentParser
from urllib.error import HTTPError
from urllib.request import urlopen

import pyshacl
import rdflib

from lib.config import Config, load_config


def main(config: Config) -> int:
    """
    Executes the validation steps

    :param config: a Config instance returned by lib.config.load_config()

    :return: 0 on successful validation
    """
    start = datetime.datetime.now()

    shacl_validate(config)
    check_links(config)

    finish = datetime.datetime.now()
    logging.info(f'Script took {finish - start}')

    return 0


def shacl_validate(config: Config) -> None:
    """
    Validates the data samples against the data shape constraint definitions

    :param config: a Config instance returned by lib.config.load_config()

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


def check_links(config: Config) -> None:
    """
    This function will check _every_ URI in the sample graphs for being able to resolve. This will catch errors on
    vocab typos, or small happy accidents on hash/slash-URI mishaps and the likes.

    :param config: a Config instance returned by lib.config.load_config()

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
    parser = ArgumentParser("Validates data samples against shape constraints, validates correctness of vocabulary")
    parser.add_argument('-c', '--config', help='Path to config.yaml', default='config.yaml')
    args = parser.parse_args()

    config = load_config(path=args.config)

    raise SystemExit(main(config))
