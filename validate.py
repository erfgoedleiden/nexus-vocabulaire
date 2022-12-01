import os

import pyshacl


def main() -> int:
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


if __name__ == '__main__':
    raise SystemExit(main())