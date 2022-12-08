import datetime
import functools
import logging
import os
import re
import ssl
from argparse import ArgumentParser

import pyshacl
import rdflib
import requests
from tqdm import tqdm
from retry import retry

from lib.config import Config, load_config
from lib.https_adapter import CustomHttpAdapter


def main(config: Config) -> int:
    """
    Executes the validation steps

    :param config: a Config instance returned by lib.config.load_config()

    :return: 0 on successful validation
    """
    start = datetime.datetime.now()

    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))

    shacl_files = os.listdir(config['validation']['shacl_dir'])

    for shacl_filename in shacl_files:
        record_type = shacl_filename.replace('.ttl', '')
        if record_type not in config['validation']['done']:
            logging.info(f"Skipping {shacl_filename}: it's not in the 'done' list in config.yaml")
            continue

        logging.info(f'Validating shape constraints for {record_type}')
        data_filename = re.sub(r'(?<!^)(?=[A-Z])', '_', shacl_filename).lower()
        data_filepath = os.path.join(config['validation']['data_dir'], data_filename)
        shacl_filepath = os.path.join(config['validation']['shacl_dir'], shacl_filename)

        if not os.path.isfile(data_filepath):
            logging.warning(f'Skipping SHACL validation for {record_type}: no data file found.')
        else:
            shacl_validate(data_filepath, shacl_filepath)
            logging.info(f'Validating URI resolvability for {data_filepath}')
            check_uris(data_filepath, config, session)

        logging.info(f'Validating URI resolvability for {shacl_filepath}')
        check_uris(shacl_filepath, config, session)

        # TODO: check consistent use of prefixes (http vs https etc.)

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


def check_uris(data_filepath: str, config: Config, session: requests.Session) -> None:
    """
    This function will check _every_ URI in the sample graphs for being able to resolve. This will catch errors on
    vocab typos, or small happy accidents on hash/slash-URI mishaps and the likes.

    :param data_filepath: path to the data graph to validate URIs

    :return: None
    """
    graph = rdflib.Graph()
    graph.parse(data_filepath)

    for triple in tqdm(graph):
        validate_triple(triple, config, session)


def validate_triple(triple: tuple, config: Config, session: requests.Session) -> None:
    for triple_part in triple:
        check = True
        for ignore_item in config['validation']['ignore_uris_containing']:
            if ignore_item in str(triple_part):
                check = False
                break

        if not check:
            continue

        # Skip literals: they do not need to be resolvable
        if not isinstance(triple_part, rdflib.URIRef):
            continue

        # Avoid requesting the same uri for an ontology hiding behind a hash
        resolvable_part = triple_part.split('#')[0]
        try:
            # Will throw an error on 400 or larger responses
            http_get(session, resolvable_part, 'text/turtle')
        except RuntimeError as e:
            logging.error(f'{triple_part} could not be resolved: {e}')
            raise

        if '#' in triple_part:
            # It's a hash uri!
            resolved_uri_graph = load_graph_from_uri(resolvable_part)

            if triple_part not in resolved_uri_graph.subjects():
                raise ValueError(f'URI {triple_part} is not a member of \n{resolvable_part}')


@retry(tries=3, delay=1, backoff=2)
@functools.lru_cache
def load_graph_from_uri(resolvable_part: str) -> rdflib.Graph:
    """
    Try loading the contents of the URI directly

    :param resolvable_part: A URI part before the hash. Because this function is cached, should not contain parts
                            including and after the #

    :return: an rdflib.Graph
    """
    resolved_uri_graph = rdflib.Graph()
    resolved_uri_graph.parse(resolvable_part)

    return resolved_uri_graph


@retry(tries=3, delay=1, backoff=2)
@functools.lru_cache
def http_get(session: requests.Session, url: str, content_type: str = 'text/html') -> str:
    """
    Simple helper function to get the text a URL given the provided content type.
    Caches the response to make sure that the content is fetched only once

    :param url: The resource to get the text from
    :param content_type: The IANA representation type of content to request

    :return: The response text
    """
    response = session.get(url=url, headers={'Accept': content_type})
    if response.status_code >= 400:
        raise RuntimeError(f'Invalid response {response.status_code} for {url}')

    return response.text


if __name__ == '__main__':
    parser = ArgumentParser("Validates data samples against shape constraints, validates correctness of vocabulary")
    parser.add_argument('-c', '--config', help='Path to config.yaml', default='config.yaml')
    args = parser.parse_args()

    config = load_config(path=args.config)

    raise SystemExit(main(config))
