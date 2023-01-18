import os

import pytest

from lib.config import load_config
from validate import shacl_validate, check_uris


def test_shacl_validation() -> None:
    data_file = 'tests/data/sample_graph.ttl'
    shacl_file = 'tests/data/shacl_def.ttl'

    with pytest.raises(AssertionError):
        shacl_validate(data_file, shacl_file)


def test_duplicate() -> None:
    config = load_config()

    # Should not raise
    graph_file_with_duplicates = os.path.join('tests', 'data', 'graph_without_duplicates.ttl')
    check_uris(graph_file_with_duplicates, config)

    # Should raise
    graph_file_with_duplicates = os.path.join('tests', 'data', 'graph_with_duplicates.ttl')
    with pytest.raises(ValueError):
        check_uris(graph_file_with_duplicates, config)
