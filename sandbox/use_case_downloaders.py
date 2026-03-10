import pkg_infra

from ontograph.client import ClientCatalog, ClientOntology
from ontograph.downloader import (
    PoochDownloaderAdapter,
    DownloadManagerAdapter)


def main():
    workspace = './'
    cache_dir = './data/out'

    # Create a session for the app
    session = pkg_infra.get_session(workspace=workspace, include_location=True)

    # Get logger from the session
    logger = session.get_logger()

    # Add simple messages to the current logger
    logger.info('This is an INFO message')
    logger.debug('This is a DEBUG message')
    logger.warning('This is a WARNING message')
    logger.error('This is an ERROR message')
    logger.critical('This is a CRITICAL message')

    # Call a given downloader from OntoGraph
    #downloader = PoochDownloaderAdapter(cache_dir=cache_dir)
    downloader = DownloadManagerAdapter(cache_dir=cache_dir)

    # Download a catalog
    catalog = ClientCatalog(cache_dir=cache_dir, downloader=downloader)
    catalog.load_catalog()

    # print the schema tree
    #catalog.print_catalog_schema_tree()

    # Download a given ontology
    client = ClientOntology(cache_dir=cache_dir, downloader=downloader)
    client.load(source='go')  # catalog download

if __name__ == '__main__':

    main()
