import argparse
import json
import logging
import os

import library


def main(zone_bundle, deployment_name, packages_root_directory, output_directory, git_repo):
    logger = logging.getLogger(__name__)
    zone_bundle_output_file = os.path.join(output_directory, 'deployed_zone.json')
    version_to_packages_map = {
        'deployment-determined': packages_root_directory,
    }
    deployed_zone_bundle = library.deploy(zone_bundle, deployment_name, version_to_packages_map, zone_bundle_output_file)
    with library.deployed_zone_bundle_manager(deployed_zone_bundle):
        icat_ip = deployed_zone_bundle['zones'][0]['icat_server']['deployment_information']['ip_address']

        complex_args = {
            'output_directory': output_directory,
            'git_repo': git_repo,
        }

        try:
            data = library.run_ansible(module_name='irods_test_jargon', complex_args=complex_args, host_list=[icat_ip])
        finally:
            library.gather(deployed_zone_bundle, output_directory)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test Jargon')
    parser.add_argument('--zone_bundle_input', type=str, required=True)
    parser.add_argument('--deployment_name', type=str, required=True)
    parser.add_argument('--packages_root_directory', type=str, required=True)
    parser.add_argument('--output_directory', type=str, required=True)
    parser.add_argument('--git_repo', type=str, required=True)
    args = parser.parse_args()

    with open(args.zone_bundle_input) as f:
        zone_bundle = json.load(f)

    library.register_log_handlers()
    library.convert_sigterm_to_exception()

    main(zone_bundle, args.deployment_name, args.packages_root_directory, args.output_directory, args.git_repo)
