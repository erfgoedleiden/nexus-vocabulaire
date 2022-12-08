import logging
import os
import time
from io import StringIO
from typing import Optional

from ruamel.yaml import YAML

# Type alias for config type
Config = dict


# Configure logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def load_config(
        path: str = 'config.yaml',
        run_id: Optional[str] = None) -> Config:
    """
    Loads 'config.yaml' from the current working directory, or somewhere else if specified

    :param path:    Path to the config yaml file
    :param run_id:  Optional manual id override for the run, mainly for testing

    :return: A Config object: a nested dictionary
    """
    yaml = YAML(typ='safe')
    with open(path) as f:
        config = yaml.load(f)['spec']

    if run_id is not None:
        config['run_id'] = run_id
    else:
        config['run_id'] = time.strftime('%Y-%m-%d_%Hh%Mm%Ss')

    # Configure logging
    logger = logging.getLogger()

    os.makedirs('logs', exist_ok=True)
    log_path = os.path.join('logs', 'logfile.txt')

    file_handler = logging.FileHandler(
        filename=log_path,
        mode='a',
    )
    logger.addHandler(file_handler)
    logging.info(f"Session has run id {config['run_id']}")

    # Validate the config: convert to text and check for template markers "~" and "{"
    string_stream = StringIO()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.default_flow_style = False
    yaml.dump(config, string_stream)
    config_as_text = string_stream.getvalue()

    if '~' in config_as_text:
        raise ValueError(f'Not all home-dir tildes "~" were substituted: \n{config_as_text}')

    return config
