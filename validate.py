import os

import pyshacl


def main() -> int:
    data_samples = os.listdir('voorbeelddata')

    for sample_file in data_samples:
        conforms, results_graph, results_text = pyshacl.validate(
            data_graph=os.path.join('voorbeelddata', sample_file),
            shacl_graph='some_shacl_file_location',
        )
        assert conforms, f'{sample_file} incorrect: {results_text}'

    return 0


if __name__ == 'main':
    raise SystemExit(main())
