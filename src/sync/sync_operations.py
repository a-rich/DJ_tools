"""This module is responsible for syncing tracks between 'USB_PATH' and the
beatcloud (upload and download). It also handles uploading the rekordbox.xml
located at 'XML_PATH' and downloading the rekordbox.xml uploaded to the
beatcloud by 'XML_IMPORT_USER' before modifying it to point to track locations
at 'USB_PATH'.
"""
from datetime import datetime
import logging
import os
from pathlib import Path

from src.sync.helpers import parse_sync_command, rewrite_xml, run_sync, webhook


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s:%(lineno)s - ' \
                           '%(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('sync_operations')


def upload_music(config):
    """This function syncs tracks from 'USB_PATH' to the beatcloud.
    'AWS_USE_DATE_MODIFIED' can be used in order to reupload tracks that
    already exist in the beatcloud but have been modified since the last time
    they were uploaded (i.e. ID3 tags have been altered).

    Args:
        config (dict): configuration object

    Raises:
        FileNotFoundError: 'USB_PATH' must exist
    """
    if not os.path.exists(config['USB_PATH']):
        raise FileNotFoundError(f'{config["USB_PATH"]} does not exist!')

    if os.environ.get('USER') != 'aweeeezy':
        logger.error('User "aweeeezy" has not yet authorized uploading music')
        return

    glob_path = Path(os.path.join(config['USB_PATH'], 'DJ Music'))
    hidden_files = set([str(p) for p in glob_path.rglob(os.path.join('**',
                                                                     '.*.*'))])
    if hidden_files:
        logger.info(f'Removed {len(hidden_files)} files...')
        for _file in hidden_files:
            logger.info(f'\t{_file}')
            os.remove(_file)

    logger.info('Syncing track collection...')
    cmd = ['aws', 's3', 'sync',
           f"{os.path.join(config['USB_PATH'], 'DJ Music')}",
           's3://dj.beatcloud.com/dj/music/']

    if config['DISCORD_URL']:
        webhook(config['DISCORD_URL'],
                content=run_sync(parse_sync_command(cmd, config, upload=True)))
    else:
        run_sync(parse_sync_command(cmd, config))


def upload_xml(config):
    """This function uploads 'XML_PATH' to beatcloud.

    Args:
        config (dict): configuration object

    Raises:
        FileNotFoundError: 'XML_PATH' file must exist 
    """
    if not os.path.exists(config['XML_PATH']):
        raise FileNotFoundError(f'{config["XML_PATH"]} does not exist!')

    logger.info(f"Uploading {config['USER']}'s rekordbox.xml...")
    dst = f's3://dj.beatcloud.com/dj/xml/{config["USER"]}/'
    cmd = f'aws s3 cp {config["XML_PATH"]} {dst}'
    logger.info(cmd)
    os.system(cmd)


def download_music(config):
    """This function syncs tracks from the beatcloud to 'USB_PATH'.
    'AWS_USE_DATE_MODIFIED' can be used in order to redownload tracks that
    already exist in 'USB_PATH' but have been modified since the last time they
    were downloaded (i.e. ID3 tags have been altered).

    Args:
        config (dict): configuration object

    Raises:
        FileNotFoundError: 'USB_PATH' must exist
    """
    if not os.path.exists(config['USB_PATH']):
        raise FileNotFoundError(f'{config["USB_PATH"]} does not exist!')

    glob_path = Path(os.path.join(config['USB_PATH'], 'DJ Music'))
    old = set([str(p) for p in glob_path.rglob(os.path.join('**', '*.*'))])
    logger.info(f"Found {len(old)} files")

    logger.info(f"Syncing remote track collection...")
    os.makedirs(os.path.join(config['USB_PATH'], 'DJ Music'), exist_ok=True)
    cmd = ['aws', 's3', 'sync', 's3://dj.beatcloud.com/dj/music/',
           f"{os.path.join(config['USB_PATH'], 'DJ Music')}"]
    run_sync(parse_sync_command(cmd, config))

    new = set([str(p) for p in glob_path.rglob(os.path.join('**', '*.*'))])
    difference = sorted(list(new.difference(old)),
                        key=lambda x: os.path.getmtime(x))
    if difference:
        logger.info(f"Found {len(difference)} new files")
        os.makedirs(os.path.join(config['LOG_DIR'], 'new'), exist_ok=True)
        now = datetime.now().strftime('%Y-%m-%dT%H.%M.%S')
        log_file = f"{now}.txt"
        with open(os.path.join(config['LOG_DIR'], 'new', log_file), 'w',
                  encoding='utf-8') as f:
            for x in difference:
                logger.info(f"\t{x}")
                f.write(f"{x}\n")


def download_xml(config):
    """This function downloads the beatcloud XML of 'XML_IMPORT_USER' and
    modifies the 'Location' field of all the tracks so that it points to the
    current user's 'USB_PATH'.

    Args:
        config (dict): configuration object

    Raises:
        FileNotFoundError: XML destination directory must exist
    """
    xml_dir = os.path.dirname(config['XML_PATH'])
    if not os.path.exists(xml_dir):
        raise FileNotFoundError(f'{xml_dir} does not exist!')

    logger.info('Syncing remote rekordbox.xml...')
    if os.name == 'nt':
        cwd = os.getcwd()
        path_parts = os.path.dirname(config['XML_PATH']).split(os.path.sep)
        root = path_parts[0]
        path_parts = path_parts[1:]
        os.chdir(root)
        for part in path_parts:
            os.makedirs(part, exist_ok=True)
            os.chdir(part)
        _file = f'{config["XML_IMPORT_USER"]}_rekordbox.xml', 
    else:
        _file = os.path.join(xml_dir,
                             f'{config["XML_IMPORT_USER"]}_rekordbox.xml')

    cmd = "aws s3 cp s3://dj.beatcloud.com/dj/xml/" \
          f"{config['XML_IMPORT_USER']}/rekordbox.xml {_file}"
    logger.info(cmd)
    os.system(cmd)
    rewrite_xml(config)

    if os.name == 'nt':
        os.chdir(cwd)
