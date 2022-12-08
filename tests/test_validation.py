import pytest

from validate import shacl_validate


def test_shacl_validation() -> None:
    data_file = 'tests/data/sample_graph.ttl'
    shacl_file = 'tests/data/shacl_def.ttl'

    with pytest.raises(AssertionError):
        shacl_validate(data_file, shacl_file)
