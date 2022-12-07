import datetime
import logging
import os
from argparse import ArgumentParser

import pyshacl
import rdflib
import requests
from retry import retry

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
        validate_triple(triple, config)


def validate_triple(triple: tuple, config: Config) -> None:
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
                    http_get(triple_part, 'text/turtle')
                except HTTPError as e:
                    logging.error(f'{triple_part} could not be resolved: {e}')
                    raise ValueError(f'{triple_part} could not be resolved: {e}')


@retry(tries=3, delay=1, backoff=2)
def http_get(url: str, content_type: str) -> str:
    """
    Simple helper function to get the text as utf-8 from a url
    :param url: The resource to get the text from
    :param content_type: The IANA representation type of content to request

    :return: The response text, parsed as UTF-8
    """
    response = requests.get(url=url, headers={'Accept': content_type})
    if response.status_code != 200:
        raise RuntimeError(f'Invalid response {response.status_code}')

    return response.text


if __name__ == '__main__':
    parser = ArgumentParser("Validates data samples against shape constraints, validates correctness of vocabulary")
    parser.add_argument('-c', '--config', help='Path to config.yaml', default='config.yaml')
    args = parser.parse_args()

    config = load_config(path=args.config)

    raise SystemExit(main(config))
