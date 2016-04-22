#!/usr/bin/python

import glob
import json
import os
import pwd
import shutil
import socket
import subprocess


def run_tests(module, result):
    put_irods_server_in_debug_mode(module)
    install_testing_dependencies()

    jargon_git_repo = module.params['git_repo']
    local_jargon_git_dir = os.path.expanduser('~/jargon')
    git_clone(jargon_git_repo, 'master', local_jargon_git_dir)
    result['jargon_commit'] = module.run_command(['git', 'rev-parse', 'HEAD'], cwd=local_jargon_git_dir)[1].strip()

    settings_repo = '/projects/irods/vsphere-testing/irods_testing_jargon'
    local_settings_git_dir = os.path.expanduser('~/irods_testing_jargon')
    git_clone(settings_repo, 'master', local_settings_git_dir)

    module.run_command("sudo su - irods -c '{0}/jargon_files/prepare-irods.sh'".format(local_settings_git_dir))
    maven_output_file = os.path.expanduser('~/maven_output.log')
    module.run_command("mvn install -fn --settings '{0}/jargon_files/maven-settings.xml' > {1}".format(local_settings_git_dir, maven_output_file), cwd=local_jargon_git_dir, use_unsafe_shell=True)

    gather_xml_reports(module)

def put_irods_server_in_debug_mode(module):
    module.run_command(['sudo', 'su', '-c', 'python /var/lib/irods/packaging/update_json.py /etc/irods/server_config.json string environment_variables,spLogLevel 11'])
    module.run_command(['sudo', 'su', '-', 'irods', '-c', '/var/lib/irods/iRODS/irodsctl restart'])

def install_testing_dependencies():
    install_os_packages(['git', 'openjdk-7-jdk', 'maven2'])

def gather_xml_reports(module):
    xml_report_dirs = ['jargon-conveyor', 'jargon-core', 'jargon-data-utils', 'jargon-httpstream', 'jargon-ruleservice', 'jargon-ticket', 'jargon-user-profile', 'jargon-user-tagging', 'jargon-workflow']
    for d in xml_report_dirs:
        path = os.path.join('/home/irodsbuild/jargon', d, 'target/surefire-reports')
        reports = glob.glob(path + '/*.xml')
        for r in reports:
            shutil.copy(r, module.params['output_directory'])

def main():
    module = AnsibleModule(
        argument_spec = dict(
            output_directory=dict(type='str', required=True),
            git_repo=dict(type='str', required=True),
        ),
        supports_check_mode=False,
    )

    result = {}
    run_tests(module, result)

    result['changed'] = True
    result['complex_args'] = module.params

    module.exit_json(**result)


from ansible.module_utils.basic import *
from ansible.module_utils.local_ansible_utils_extension import *
main()
