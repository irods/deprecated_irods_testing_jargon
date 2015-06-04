#!/usr/bin/python

import glob
import json
import os
import pwd
import shutil
import socket
import subprocess


def run_tests(module, result):
    install_testing_dependencies(module)

    jargon_git_repo = 'https://github.com/DICE-UNC/jargon'
    local_jargon_git_dir = os.path.expanduser('~/jargon')
    git_clone(module, jargon_git_repo, local_jargon_git_dir, commit='master')
    _, jargon_commit, _ = module.run_command('git rev-parse HEAD', cwd=local_jargon_git_dir)
    result['jargon_commit'] = jargon_commit.strip()

    settings_repo = '/projects/irods/vsphere-testing/irods_jargon_testing'
    local_settings_git_dir = os.path.expanduser('~/irods_jargon_testing')
    git_clone(module, settings_repo, local_settings_git_dir)

    module.run_command("sudo su - irods -c '{0}/jargon_files/prepare-irods.sh'".format(local_settings_git_dir))
    maven_output_file = os.path.expanduser('~/maven_output.log')
    module.run_command("mvn install -fn --settings '{0}/jargon_files/maven-settings.xml' > {1}".format(local_settings_git_dir, maven_output_file), cwd=local_jargon_git_dir, use_unsafe_shell=True)

    gather_xml_reports(module)

def install_testing_dependencies(module):
    module.run_command('sudo apt-get update', check_rc=True)
    packages = ['git', 'openjdk-7-jdk', 'maven2']
    install_command = ['sudo', 'apt-get', 'install', '-y'] + packages
    module.run_command(install_command, check_rc=True)

def git_clone(module, repo, local_dir, commit=None):
    module.run_command('git clone --recursive {0} {1}'.format(repo, local_dir), check_rc=True)
    if commit:
        module.run_command('git checkout {0}'.format(commit), cwd=local_dir, check_rc=True)

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
        ),
        supports_check_mode=False,
    )

    result = {}
    run_tests(module, result)

    result['changed'] = True
    result['complex_args'] = module.params

    module.exit_json(**result)


from ansible.module_utils.basic import *
main()
