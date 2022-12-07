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

    data_samples = os.listdir('voorbeelddata')
    for sample_file in data_samples:
        shacl_filename = ''.join([name.capitalize() for name in sample_file.split('_')])
        record_type = shacl_filename.replace('.ttl', '')

        if record_type not in config['validation']['done']:
            logging.info(f"Skipping {shacl_filename}: it's not in the 'done' list in config.yaml")
            continue

        logging.info(f'Validating shape constraints for {record_type}')
        sample_filepath = os.path.join('voorbeelddata', sample_file)
        shacl_filepath = os.path.join('shacl', shacl_filename)
        shacl_validate(sample_filepath, shacl_filepath)

        logging.info(f'Validating URI resolvability for {record_type}')
        check_uris(shacl_filepath, config)
        check_uris(sample_filepath, config)

    finish = datetime.datetime.now()
    logging.info(f'Script took {finish - start}')

    return 0


def shacl_validate(data_filepath: str, shacl_filepath: str) -> None:
    """
    Validates the data samples against the data shape constraint definitions

    :param data_filepath:   path to a data graph file to validate
    :param shacl_filepath:  path to the SHACL definition to validate against

    :return: None
    """

    conforms, results_graph, results_text = pyshacl.validate(
        data_graph=data_filepath,
        shacl_graph=shacl_filepath,
    )
    assert conforms, f'{data_filepath} incorrect: {results_text}'


def check_uris(data_filepath: str, config: Config) -> None:
    """
    This function will check _every_ URI in the sample graphs for being able to resolve. This will catch errors on
    vocab typos, or small happy accidents on hash/slash-URI mishaps and the likes.

    :param data_filepath: path to the data graph to validate URIs

    :return: None
    """
    graph = rdflib.Graph()
    graph.parse(data_filepath)

    for triple in graph:
        for triple_part in triple:
            check = True
            for ignore_item in config['validation']['ignore_uris_containing']:
                if ignore_item in str(triple_part):
                    check = False
                    break

            if not check:
                continue

            if isinstance(triple_part, rdflib.URIRef):
                # TODO: parse response from URI to match hash uris against subjects in the graph in order to
                #  validate

                # urlopen will throw an error on 400 or larger responses
                try:
                    urlopen(triple_part).read()
                except HTTPError as e:
                    logging.error(f'{triple_part} could not be resolved: {e}')
                    raise ValueError(f'{triple_part} could not be resolved: {e}')


if __name__ == '__main__':
    parser = ArgumentParser("Validates data samples against shape constraints, validates correctness of vocabulary")
    parser.add_argument('-c', '--config', help='Path to config.yaml', default='config.yaml')
    args = parser.parse_args()

    config = load_config(path=args.config)

    raise SystemExit(main(config))
