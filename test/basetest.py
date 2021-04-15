#!/usr/bin/env python

"base test script"

# pylint: disable=import-error
# pylint: disable=invalid-name
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-lines
# pylint: disable=too-many-public-methods

# https://docs.python.org/3/
import contextlib
import os
import re
import subprocess
import tempfile
import time
import unittest

# https://pypi.org/project/pexpect/
import pexpect


##############################################################################
# constants

EXIT_DELAY = 0.1  # seconds

DEFAULT_TIMEOUT = 2  # seconds


##############################################################################
# patterns

RE_PROMPT_USER = re.compile(
    b'''
    \r\n           # start of line
    \x1b\\]0;      # escape sequence: title begin
    ([^\x07]+)     # group 1: title
    \x07           # escape sequence: title end
    \x1b\\[01;32m  # escape sequence: bold green
    ([^\x1b]+)     # group 2: username@hostname
    \x1b\\[00m     # escape sequence: clear
    :              # colon
    \x1b\\[01;34m  # escape sequence: bold blue
    ([^\x1b]+)     # group 3: current working directory
    \x1b\\[00m     # escape sequence: clear
    \\$            # dollar sign
    \\             # space
    ''', re.VERBOSE)

RE_PROMPT_ROOT = re.compile(
    b'''
    \r\n     # start of line
    ([^:]+)  # group 1: username@hostname
    :        # colon
    ([^#]+)  # path
    \\#      # pound sign
    \\       # space
    ''', re.VERBOSE)

RE_PROMPT_BASE = re.compile(
    b'''
    \r\n        # start of line
    \x1b\\]2;   # escape sequence: title begin
    ([^\x07]+)  # group 1: title
    \x07        # escape sequence: title end
    \\[         # left bracket
    ([^]]+)     # group 2: base label
    \\]         # right bracket
    \\          # space
    ([^$#]*)    # group 3: relative path
    ([$#])      # group 4: dollar sign or pound sign
    \\          # space
    ''', re.VERBOSE)

RE_PROMPT_BASE_OUT = re.compile(
    b'''
    \r\n        # start of line
    \x1b\\]2;   # escape sequence: title begin
    ([^\x07]+)  # group 1: title
    \x07        # escape sequence: title end
    \\(         # left parenthesis
    ([^)]+)     # group 2: base label
    \\)         # right parenthesis
    \\          # space
    ([^$#]*)    # group 3: path
    ([$#])      # group 4: dollar sign or pound sign
    \\          # space
    ''', re.VERBOSE)

RE_PROMPT_BASE_NOTITLE = re.compile(
    b'''
    \r\n      # start of line
    \\[       # left bracket
    ([^]]+)   # group 1: base label
    \\]       # right bracket
    \\        # space
    ([^$#]*)  # group 2: relative path
    ([$#])    # group 3: dollar sign or pound sign
    \\        # space
    ''', re.VERBOSE)

RE_USAGE = re.compile(
    b'''
    \r\n         # start of line
    Usage:       # usage indicator
    \\           # space
    base         # start of usage text
    ''', re.VERBOSE)

RE_VERSION = re.compile(
    b'''
    \r\n                  # start of line
    base                  # program name
    \\                    # space
    (\\d+\\.\\d+\\.\\d+)  # group 1: program version
    \r\n                  # end of line
    ''', re.VERBOSE)


##############################################################################
# library

def mkdir_p(path):
    if not os.path.exists(path):
        mkdir_p(os.path.dirname(path))
        os.mkdir(path, 0o755)


def sudo_mkdir_p(path):
    subprocess.run(['sudo', 'mkdir', '-p', path], check=True)


def sudo_rm_rf(path):
    subprocess.run(['sudo', 'rm', '-rf', path], check=True)


@contextlib.contextmanager
def temp_project(subdirs=None):
    with tempfile.TemporaryDirectory() as tempdir:
        for subdir in subdirs or ('src/project', 'test'):
            mkdir_p(os.path.join(tempdir, subdir))
        yield tempdir


@contextlib.contextmanager
def temp_project_go(link=None, versions=None):
    if versions is None:
        versions = ('1.14.15', '1.15.11', '1.16.3')
    for version in versions:
        sudo_mkdir_p(os.path.join('/usr/local/opt', f'go-{version}', 'bin'))

    with tempfile.TemporaryDirectory() as tempdir:
        mkdir_p(os.path.join(tempdir, 'bin'))
        projdir = os.path.join(tempdir, 'src', 'project')
        mkdir_p(projdir)
        if link is not None:
            os.symlink(
                os.path.join('/usr/local/opt', f'go-{link}'),
                os.path.join(projdir, '.go'),
                True,
            )
        yield projdir

    sudo_rm_rf('/usr/local/opt')


@contextlib.contextmanager
def temp_project_python(link=None, versions=None):
    with tempfile.TemporaryDirectory() as tempdir:
        for version in versions or ('3.7.10', '3.8.9', '3.9.4'):
            mkdir_p(os.path.join(tempdir, f'virtualenv-{version}'))
        if link is not None:
            os.symlink(
                f'virtualenv-{link}',
                os.path.join(tempdir, 'virtualenv'),
                True,
            )
        yield tempdir


@contextlib.contextmanager
def temp_home_dir():
    home_path = os.getenv('HOME')
    with tempfile.TemporaryDirectory(dir=home_path) as home_dir:
        yield home_dir, b'~' + home_dir[len(home_path):].encode()


##############################################################################
# tests

class TestBase(unittest.TestCase):

    def setUp(self):
        self.shell = pexpect.spawn('/bin/bash')
        self.expect(RE_PROMPT_USER)

    def tearDown(self):
        self.shell.sendline('exit')
        time.sleep(EXIT_DELAY)
        if self.shell.isalive():
            self.shell.sendline('exit')
            time.sleep(EXIT_DELAY)
            if self.shell.isalive():
                self.shell.close(force=True)

    # library ################################################################

    def assertBasePrompt(self, label, relpath, *, root=False):
        self.expect(RE_PROMPT_BASE)
        self.assertEqual(
            self.shell.match.group(1), b'[' + label + b'] ' + relpath)
        self.assertEqual(self.shell.match.group(2), label)
        self.assertEqual(self.shell.match.group(3), relpath)
        self.assertEqual(
            self.shell.match.group(4), b'#' if root else b'$')

    def assertBasePromptNoTitle(self, label, relpath, *, root=False):
        self.expect(RE_PROMPT_BASE_NOTITLE)
        self.assertEqual(self.shell.match.group(1), label)
        self.assertEqual(self.shell.match.group(2), relpath)
        self.assertEqual(
            self.shell.match.group(3), b'#' if root else b'$')

    def assertBasePromptOut(self, label, path, *, root=False):
        self.expect(RE_PROMPT_BASE_OUT)
        self.assertEqual(
            self.shell.match.group(1), b'(' + label + b') ' + path)
        self.assertEqual(self.shell.match.group(2), label)
        self.assertEqual(self.shell.match.group(3), path)
        self.assertEqual(
            self.shell.match.group(4), b'#' if root else b'$')

    def assertFound(self, name):
        self.shell.sendline(f'declare -p {name}')
        self.assertStatus(0)

    def assertFunction(self, name):
        self.shell.sendline(f'type -t {name} || echo notfound')
        self.expect_exact(b'\r\nfunction\r\n')

    def assertNotFound(self, name):
        self.shell.sendline(f'type -t {name} || echo notfound')
        self.expect_exact(b'\r\nnotfound\r\n')

    def assertRootPrompt(self):
        self.expect(RE_PROMPT_ROOT)

    def assertStatus(self, status):
        self.shell.sendline('echo $?')
        self.expect_exact(f'\r\n{status}\r\n'.encode())

    def assertUserPrompt(self):
        self.expect(RE_PROMPT_USER)

    def assertVersion(self, version=None):
        self.expect(RE_VERSION)
        if version is not None:
            self.assertEqual(self.shell.match.group(1), version)

    def assertUsage(self):
        self.expect(RE_USAGE)

    def expect(self, pattern, *, timeout=DEFAULT_TIMEOUT):
        self.shell.expect(pattern, timeout=timeout)

    def expect_exact(self, pattern, *, timeout=DEFAULT_TIMEOUT):
        self.shell.expect_exact(pattern, timeout=timeout)

    def getPID(self):
        self.shell.sendline('echo $$')
        self.expect(b'\r\n(\\d+)\r\n')
        return self.shell.match.group(1)

    def sendline(self, line):
        self.shell.sendline(line)

    # --version argument #####################################################

    def test_base_version(self):
        pid_initial = self.getPID()
        self.sendline('base --version')
        self.assertVersion()
        self.assertStatus(0)
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_version(self):
        pid_initial = self.getPID()
        self.sendline('source base --version')
        self.assertVersion()
        self.assertStatus(0)
        self.assertNotFound('_base_help')
        self.assertNotFound('_base_load_env')
        self.assertNotFound('BASE_VERSION')
        self.assertEqual(self.getPID(), pid_initial)

    def test_base_activate_version(self):
        pid_initial = self.getPID()
        self.sendline('base_activate --version')
        self.assertVersion()
        self.assertStatus(0)
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_activate_version(self):
        pid_initial = self.getPID()
        self.sendline('source base_activate --version')
        self.assertVersion()
        self.assertStatus(0)
        self.assertNotFound('_base_help')
        self.assertNotFound('BASE_VERSION')
        self.assertEqual(self.getPID(), pid_initial)

    # --help argument ########################################################

    def test_base_help(self):
        pid_initial = self.getPID()
        self.sendline('base --help')
        self.assertUsage()
        self.assertStatus(0)
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_help(self):
        pid_initial = self.getPID()
        self.sendline('source base --help')
        self.assertUsage()
        self.assertStatus(0)
        self.assertNotFound('_base_help')
        self.assertNotFound('_base_load_env')
        self.assertNotFound('BASE_VERSION')
        self.assertEqual(self.getPID(), pid_initial)

    def test_base_activate_help(self):
        pid_initial = self.getPID()
        self.sendline('base_activate --help')
        self.assertUsage()
        self.assertStatus(0)
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_activate_help(self):
        pid_initial = self.getPID()
        self.sendline('source base_activate --help')
        self.assertUsage()
        self.assertStatus(0)
        self.assertNotFound('_base_help')
        self.assertNotFound('BASE_VERSION')
        self.assertEqual(self.getPID(), pid_initial)

    # base_activate normal execution #########################################

    def test_base_activate_normal_execution(self):
        pid_initial = self.getPID()
        self.sendline('base_activate')
        self.assertUsage()
        self.assertStatus(2)
        self.assertEqual(self.getPID(), pid_initial)

    # too many arguments #####################################################

    def test_base_too_many_args(self):
        pid_initial = self.getPID()
        self.sendline('base one two')
        self.assertUsage()
        self.assertStatus(2)
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_too_many_args(self):
        pid_initial = self.getPID()
        self.sendline('source base one two')
        self.assertUsage()
        self.assertStatus(2)
        self.assertNotFound('_base_help')
        self.assertNotFound('BASE_VERSION')
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_activate_too_many_args(self):
        pid_initial = self.getPID()
        self.sendline('source base_activate one two')
        self.assertUsage()
        self.assertStatus(2)
        self.assertNotFound('_base_help')
        self.assertNotFound('_base_load_env')
        self.assertNotFound('BASE_VERSION')
        self.assertEqual(self.getPID(), pid_initial)

    # nested bases ###########################################################

    def test_base_nested(self):
        self.sendline('cd /usr')
        self.assertUserPrompt()
        pid_initial = self.getPID()
        self.sendline('base')
        self.assertBasePrompt(b'usr', b'')
        pid_base1 = self.getPID()
        self.assertBasePrompt(b'usr', b'')
        self.assertNotEqual(pid_base1, pid_initial)
        self.sendline('cd local')
        self.assertBasePrompt(b'usr', b'local')
        self.sendline('base')
        self.assertBasePrompt(b'local', b'')
        pid_base2 = self.getPID()
        self.assertBasePrompt(b'local', b'')
        self.assertNotEqual(pid_base2, pid_base1)
        self.assertNotEqual(pid_base2, pid_initial)
        self.sendline('exit')
        self.assertBasePrompt(b'usr', b'local')
        self.assertEqual(self.getPID(), pid_base1)
        self.sendline('exit')
        self.assertUserPrompt()
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_nested(self):
        self.sendline('cd /usr')
        self.assertUserPrompt()
        pid_initial = self.getPID()
        self.sendline('source base')
        self.assertBasePrompt(b'usr', b'')
        pid_base1 = self.getPID()
        self.assertBasePrompt(b'usr', b'')
        self.assertNotEqual(pid_base1, pid_initial)
        self.sendline('cd local')
        self.assertBasePrompt(b'usr', b'local')
        self.sendline('source base')
        self.assertBasePrompt(b'local', b'')
        pid_base2 = self.getPID()
        self.assertBasePrompt(b'local', b'')
        self.assertNotEqual(pid_base2, pid_base1)
        self.assertNotEqual(pid_base2, pid_initial)
        self.sendline('exit')
        self.assertBasePrompt(b'usr', b'local')
        self.assertEqual(self.getPID(), pid_base1)
        self.sendline('exit')
        self.assertUserPrompt()
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_activate_nested(self):
        self.sendline('cd /usr')
        self.assertUserPrompt()
        pid_initial = self.getPID()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'usr', b'')
        self.assertEqual(self.getPID(), pid_initial)
        self.sendline('source base_activate')
        self.expect_exact(
            b'\r\nerror: nested bases require a new Bash shell\r\n')

    # BASE_VERSION environment variable ######################################

    def test_base_version_variable(self):
        self.sendline('base')
        self.assertFound('BASE_VERSION')

    def test_source_base_version_variable(self):
        self.sendline('source base')
        self.assertFound('BASE_VERSION')

    def test_source_base_activate_version_variable(self):
        self.sendline('source base_activate')
        self.assertFound('BASE_VERSION')
        self.sendline('base_deactivate')
        self.assertNotFound('BASE_VERSION')

    # BASE_MODE environment variable #########################################

    def test_base_mode_variable(self):
        self.sendline('base')
        self.sendline('echo ${BASE_MODE}')
        self.expect_exact(b'\r\nNEWENV\r\n')

    def test_source_base_mode_variable(self):
        self.sendline('source base')
        self.sendline('echo ${BASE_MODE}')
        self.expect_exact(b'\r\nCPYENV\r\n')

    def test_source_base_activate_mode_variable(self):
        self.sendline('source base_activate')
        self.sendline('echo ${BASE_MODE}')
        self.expect_exact(b'\r\nCURENV\r\n')
        self.sendline('base_deactivate')
        self.assertNotFound('BASE_MODE')

    # BASE environment variable ##############################################

    def test_base_variable(self):
        self.sendline('cd /tmp')
        self.sendline('base')
        self.sendline('echo "${BASE}"')
        self.expect_exact(b'\r\n/tmp\r\n')

    def test_source_base_variable(self):
        self.sendline('cd /tmp')
        self.sendline('source base')
        self.sendline('echo "${BASE}"')
        self.expect_exact(b'\r\n/tmp\r\n')

    def test_source_base_activate_variable(self):
        self.sendline('cd /tmp')
        self.sendline('source base_activate')
        self.sendline('echo "${BASE}"')
        self.expect_exact(b'\r\n/tmp\r\n')
        self.sendline('base_deactivate')
        self.assertNotFound('BASE')

    # BASE_LABEL environment variable ########################################

    def test_base_label_default(self):
        self.sendline('cd /tmp')
        self.sendline('base')
        self.sendline('echo "${BASE_LABEL}"')
        self.expect_exact(b'\r\ntmp\r\n')

    def test_base_label_cli(self):
        self.sendline('base cli')
        self.sendline('echo "${BASE_LABEL}"')
        self.expect_exact(b'\r\ncli\r\n')

    def test_source_base_label_default(self):
        self.sendline('cd /tmp')
        self.sendline('source base')
        self.sendline('echo "${BASE_LABEL}"')
        self.expect_exact(b'\r\ntmp\r\n')

    def test_source_base_label_cli(self):
        self.sendline('source base cli')
        self.sendline('echo "${BASE_LABEL}"')
        self.expect_exact(b'\r\ncli\r\n')

    def test_source_base_activate_label_default(self):
        self.sendline('cd /tmp')
        self.sendline('source base_activate')
        self.sendline('echo "${BASE_LABEL}"')
        self.expect_exact(b'\r\ntmp\r\n')
        self.sendline('base_deactivate')
        self.assertNotFound('BASE_LABEL')

    def test_source_base_activate_label_cli(self):
        self.sendline('source base_activate cli')
        self.sendline('echo "${BASE_LABEL}"')
        self.expect_exact(b'\r\ncli\r\n')
        self.sendline('base_deactivate')
        self.assertNotFound('BASE_LABEL')

    # environment variables ##################################################

    def test_base_exported_variable(self):
        self.sendline('export TEST_EXP_VAR=foo')
        self.sendline('base')
        self.sendline('echo "${TEST_EXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')
        self.sendline('exit')
        self.sendline('echo "${TEST_EXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_exported_variable(self):
        self.sendline('export TEST_EXP_VAR=foo')
        self.sendline('source base')
        self.sendline('echo "${TEST_EXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')
        self.sendline('exit')
        self.sendline('echo "${TEST_EXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_activate_exported_variable(self):
        self.sendline('export TEST_EXP_VAR=foo')
        self.sendline('source base_activate')
        self.sendline('echo "${TEST_EXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')
        self.sendline('base_deactivate')
        self.sendline('echo "${TEST_EXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')

    def test_base_non_exported_variable(self):
        self.sendline('TEST_NONEXP_VAR=foo')
        self.sendline('base')
        self.assertNotFound('TEST_NONEXP_VAR')
        self.sendline('exit')
        self.sendline('echo "${TEST_NONEXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_non_exported_variable(self):
        self.sendline('TEST_NONEXP_VAR=foo')
        self.sendline('source base')
        self.sendline('echo "${TEST_NONEXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')
        self.sendline('exit')
        self.sendline('echo "${TEST_NONEXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_activate_non_exported_variable(self):
        self.sendline('TEST_NONEXP_VAR=foo')
        self.sendline('source base_activate')
        self.sendline('echo "${TEST_NONEXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')
        self.sendline('base_deactivate')
        self.sendline('echo "${TEST_NONEXP_VAR}"')
        self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_newline_variable(self):
        self.sendline("TEST_NL_VAR=$'one\\n\"two\\'\\tthree\"\\nfour'")
        self.sendline('source base')
        self.sendline('echo "${TEST_NL_VAR}"')
        self.expect_exact(b"\r\none\r\n\"two'\tthree\"\r\nfour\r\n")

    # base_deactivate ########################################################

    def test_base_deactivate_function(self):
        self.sendline('base')
        self.assertFunction('base_deactivate')
        self.sendline('base_deactivate')
        self.assertNotFound('base_deactivate')

    def test_source_base_deactivate_function(self):
        self.sendline('source base')
        self.assertFunction('base_deactivate')
        self.sendline('base_deactivate')
        self.assertNotFound('base_deactivate')

    def test_source_base_activate_deactivate_function(self):
        self.sendline('source base_activate')
        self.assertFunction('base_deactivate')
        self.sendline('base_deactivate')
        self.assertNotFound('base_deactivate')

    def test_base_deactivate_pid(self):
        pid_initial = self.getPID()
        self.sendline('base')
        self.assertNotEqual(self.getPID(), pid_initial)
        self.sendline('base_deactivate')
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_deactivate_pid(self):
        pid_initial = self.getPID()
        self.sendline('source base')
        self.assertNotEqual(self.getPID(), pid_initial)
        self.sendline('base_deactivate')
        self.assertEqual(self.getPID(), pid_initial)

    def test_source_base_activate_deactivate_pid(self):
        pid_initial = self.getPID()
        self.sendline('source base_activate')
        self.assertEqual(self.getPID(), pid_initial)
        self.sendline('base_deactivate')
        self.assertEqual(self.getPID(), pid_initial)

    # user prompt ############################################################

    def test_base_user_prompt_base(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'')

    def test_source_base_user_prompt_base(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'')

    def test_source_base_activate_user_prompt_base(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'')

    def test_base_user_prompt_under_base(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')

    def test_source_base_user_prompt_under_base(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')

    def test_source_base_activate_user_prompt_under_base(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')

    def test_base_user_prompt_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('cd')
        self.assertBasePromptOut(b'tmp', b'~')

    def test_source_base_user_prompt_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('cd')
        self.assertBasePromptOut(b'tmp', b'~')

    def test_source_base_activate_user_prompt_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('cd')
        self.assertBasePromptOut(b'tmp', b'~')

    def test_base_user_prompt_under_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'')
        with temp_home_dir() as (home_dir, home_rel):
            self.sendline(f'cd {home_dir}')
            self.assertBasePromptOut(b'tmp', home_rel)

    def test_source_base_user_prompt_under_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'')
        with temp_home_dir() as (home_dir, home_rel):
            self.sendline(f'cd {home_dir}')
            self.assertBasePromptOut(b'tmp', home_rel)

    def test_source_base_activate_user_prompt_under_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'')
        with temp_home_dir() as (home_dir, home_rel):
            self.sendline(f'cd {home_dir}')
            self.assertBasePromptOut(b'tmp', home_rel)

    def test_base_user_prompt_out(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('cd /usr/local')
        self.assertBasePromptOut(b'tmp', b'/usr/local')

    def test_source_base_user_prompt_out(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('cd /usr/local')
        self.assertBasePromptOut(b'tmp', b'/usr/local')

    def test_source_base_activate_user_prompt_out(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('cd /usr/local')
        self.assertBasePromptOut(b'tmp', b'/usr/local')

    def test_base_user_prompt_no_title(self):
        self.sendline('export BASE_NO_TITLE=1')
        self.assertUserPrompt()
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('base')
        self.assertBasePromptNoTitle(b'tmp', b'')

    def test_source_base_user_prompt_no_title(self):
        self.sendline('export BASE_NO_TITLE=1')
        self.assertUserPrompt()
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base')
        self.assertBasePromptNoTitle(b'tmp', b'')

    def test_source_base_activate_user_prompt_no_title(self):
        self.sendline('export BASE_NO_TITLE=1')
        self.assertUserPrompt()
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base_activate')
        self.assertBasePromptNoTitle(b'tmp', b'')

    def test_base_user_prompt_no_title_mid(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('BASE_NO_TITLE=1')
        self.assertBasePromptNoTitle(b'tmp', b'')

    def test_source_base_user_prompt_no_title_mid(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('BASE_NO_TITLE=1')
        self.assertBasePromptNoTitle(b'tmp', b'')

    def test_source_base_activate_user_prompt_no_title_mid(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('BASE_NO_TITLE=1')
        self.assertBasePromptNoTitle(b'tmp', b'')

    def test_base_user_prompt_cli(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('base cli')
        self.assertBasePrompt(b'cli', b'')

    def test_source_base_user_prompt_cli(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base cli')
        self.assertBasePrompt(b'cli', b'')

    def test_source_base_activate_user_prompt_cli(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base_activate cli')
        self.assertBasePrompt(b'cli', b'')

    # root prompt ############################################################

    def test_base_root_prompt_base(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'', root=True)

    def test_source_base_root_prompt_base(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'', root=True)

    def test_source_base_activate_root_prompt_base(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'', root=True)

    def test_base_root_prompt_under_base(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('sudo su')
            self.assertRootPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'', root=True)
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project', root=True)

    def test_source_base_root_prompt_under_base(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('sudo su')
            self.assertRootPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'', root=True)
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project', root=True)

    def test_source_base_activate_root_prompt_under_base(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('sudo su')
            self.assertRootPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'', root=True)
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project', root=True)

    def test_base_root_prompt_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('cd')
        self.assertBasePromptOut(b'tmp', b'~', root=True)

    def test_source_base_root_prompt_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('cd')
        self.assertBasePromptOut(b'tmp', b'~', root=True)

    def test_source_base_activate_root_prompt_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('cd')
        self.assertBasePromptOut(b'tmp', b'~', root=True)

    def test_base_root_prompt_under_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('mkdir -p /root/basetest')
        self.assertRootPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('cd /root/basetest')
        self.assertBasePromptOut(b'tmp', b'~/basetest', root=True)
        self.sendline('cd')
        self.sendline('rmdir -f /root/basetest')

    def test_source_base_root_prompt_under_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('mkdir -p /root/basetest')
        self.assertRootPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('cd /root/basetest')
        self.assertBasePromptOut(b'tmp', b'~/basetest', root=True)
        self.sendline('cd')
        self.sendline('rmdir -f /root/basetest')

    def test_source_base_activate_root_prompt_under_home(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('mkdir -p /root/basetest')
        self.assertRootPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('cd /root/basetest')
        self.assertBasePromptOut(b'tmp', b'~/basetest', root=True)
        self.sendline('cd')
        self.sendline('rmdir -f /root/basetest')

    def test_base_root_prompt_out(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('cd /usr/local')
        self.assertBasePromptOut(b'tmp', b'/usr/local', root=True)

    def test_source_base_root_prompt_out(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('cd /usr/local')
        self.assertBasePromptOut(b'tmp', b'/usr/local', root=True)

    def test_source_base_activate_root_prompt_out(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('cd /usr/local')
        self.assertBasePromptOut(b'tmp', b'/usr/local', root=True)

    def test_base_root_prompt_no_title(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('export BASE_NO_TITLE=1')
        self.assertRootPrompt()
        self.sendline('base')
        self.assertBasePromptNoTitle(b'tmp', b'', root=True)

    def test_source_base_root_prompt_no_title(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('export BASE_NO_TITLE=1')
        self.assertRootPrompt()
        self.sendline('source base')
        self.assertBasePromptNoTitle(b'tmp', b'', root=True)

    def test_source_base_activate_root_prompt_no_title(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('export BASE_NO_TITLE=1')
        self.assertRootPrompt()
        self.sendline('source base_activate')
        self.assertBasePromptNoTitle(b'tmp', b'', root=True)

    def test_base_root_prompt_no_title_mid(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('export BASE_NO_TITLE=1')
        self.assertBasePromptNoTitle(b'tmp', b'', root=True)

    def test_source_base_root_prompt_no_title_mid(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('export BASE_NO_TITLE=1')
        self.assertBasePromptNoTitle(b'tmp', b'', root=True)

    def test_source_base_activate_root_prompt_no_title_mid(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'', root=True)
        self.sendline('export BASE_NO_TITLE=1')
        self.assertBasePromptNoTitle(b'tmp', b'', root=True)

    def test_base_root_prompt_cli(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('base cli')
        self.assertBasePrompt(b'cli', b'', root=True)

    def test_source_base_root_prompt_cli(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base cli')
        self.assertBasePrompt(b'cli', b'', root=True)

    def test_source_base_activate_root_prompt_cli(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('sudo su')
        self.assertRootPrompt()
        self.sendline('source base_activate cli')
        self.assertBasePrompt(b'cli', b'', root=True)

    # PROMPT_COMMAND #########################################################

    def test_base_prompt_command(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('ps_hook () { touch hooked ; }')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('PROMPT_COMMAND="ps_hook;${PROMPT_COMMAND}"')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('test -f hooked && echo found')
            self.expect_exact(b'\r\nfound\r\n')

    def test_source_base_prompt_command(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('ps_hook () { touch hooked ; }')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('PROMPT_COMMAND="ps_hook;${PROMPT_COMMAND}"')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('test -f hooked && echo found')
            self.expect_exact(b'\r\nfound\r\n')

    def test_source_base_activate_prompt_command(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('ps_hook () { touch hooked ; }')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('PROMPT_COMMAND="ps_hook;${PROMPT_COMMAND}"')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('test -f hooked && echo found')
            self.expect_exact(b'\r\nfound\r\n')

    # bcd ####################################################################

    def test_base_bcd_function(self):
        self.sendline('base')
        self.assertFunction('bcd')
        self.sendline('exit')
        self.assertNotFound('bcd')

    def test_source_base_bcd_function(self):
        self.sendline('source base')
        self.assertFunction('bcd')
        self.sendline('exit')
        self.assertNotFound('bcd')

    def test_source_base_activate_bcd_function(self):
        self.sendline('source base_activate')
        self.assertFunction('bcd')
        self.sendline('base_deactivate')
        self.assertNotFound('bcd')

    def test_base_bcd_no_args(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')
            self.sendline('bcd')
            self.assertBasePrompt(tempdir_name, b'')

    def test_source_base_bcd_no_args(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')
            self.sendline('bcd')
            self.assertBasePrompt(tempdir_name, b'')

    def test_source_base_activate_bcd_no_args(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')
            self.sendline('bcd')
            self.assertBasePrompt(tempdir_name, b'')

    def test_base_bcd_one_level(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')
            self.sendline('bcd test')
            self.assertBasePrompt(tempdir_name, b'test')

    def test_source_base_bcd_one_level(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')
            self.sendline('bcd test')
            self.assertBasePrompt(tempdir_name, b'test')

    def test_source_base_activate_bcd_one_level(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')
            self.sendline('bcd test')
            self.assertBasePrompt(tempdir_name, b'test')

    def test_base_bcd_two_levels(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd test')
            self.assertBasePrompt(tempdir_name, b'test')
            self.sendline('bcd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')

    def test_source_base_bcd_two_levels(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd test')
            self.assertBasePrompt(tempdir_name, b'test')
            self.sendline('bcd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')

    def test_source_base_activate_bcd_two_levels(self):
        with temp_project() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('cd test')
            self.assertBasePrompt(tempdir_name, b'test')
            self.sendline('bcd src/project')
            self.assertBasePrompt(tempdir_name, b'src/project')

    def test_base_bcd_too_many_args(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('bcd one two')
        self.expect_exact(b'\r\nusage: bcd')
        self.assertStatus(2)
        self.assertBasePrompt(b'tmp', b'')

    def test_source_base_bcd_too_many_args(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('bcd one two')
        self.expect_exact(b'\r\nusage: bcd')
        self.assertStatus(2)
        self.assertBasePrompt(b'tmp', b'')

    def test_source_base_activate_bcd_too_many_args(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('bcd one two')
        self.expect_exact(b'\r\nusage: bcd')
        self.assertStatus(2)
        self.assertBasePrompt(b'tmp', b'')

    def test_base_bcd_no_exist(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('bcd noexist')
        self.expect_exact(b'No such file or directory\r\n')
        self.assertStatus(1)
        self.assertBasePrompt(b'tmp', b'')

    def test_source_base_bcd_no_exist(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('bcd noexist')
        self.expect_exact(b'No such file or directory\r\n')
        self.assertStatus(1)
        self.assertBasePrompt(b'tmp', b'')

    def test_source_base_activate_bcd_no_exist(self):
        self.sendline('cd /tmp')
        self.assertUserPrompt()
        self.sendline('source base_activate')
        self.assertBasePrompt(b'tmp', b'')
        self.sendline('bcd noexist')
        self.expect_exact(b'No such file or directory\r\n')
        self.assertStatus(1)
        self.assertBasePrompt(b'tmp', b'')

    def test_base_bcd_not_directory(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('touch basetest')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('bcd basetest')
            self.expect_exact(b'Not a directory\r\n')
            self.assertStatus(1)
            self.assertBasePrompt(tempdir_name, b'')

    # bcd completion #########################################################

    def test_base_bcd_complete_single(self):
        self.sendline('cd /usr')
        self.sendline('base')
        self.sendline('_base_bcd_complete "" "b"')
        self.sendline('echo "${#COMPREPLY[@]}"')
        self.expect_exact(b'\r\n1\r\n')
        self.sendline('echo "${COMPREPLY[@]}"')
        self.expect_exact(b'\r\nbin\r\n')

    def test_source_base_bcd_complete_single(self):
        self.sendline('cd /usr')
        self.sendline('source base')
        self.sendline('_base_bcd_complete "" "b"')
        self.sendline('echo "${#COMPREPLY[@]}"')
        self.expect_exact(b'\r\n1\r\n')
        self.sendline('echo "${COMPREPLY[@]}"')
        self.expect_exact(b'\r\nbin\r\n')

    def test_source_base_activate_bcd_complete_single(self):
        self.sendline('cd /usr')
        self.sendline('source base_activate')
        self.sendline('_base_bcd_complete "" "b"')
        self.sendline('echo "${#COMPREPLY[@]}"')
        self.expect_exact(b'\r\n1\r\n')
        self.sendline('echo "${COMPREPLY[@]}"')
        self.expect_exact(b'\r\nbin\r\n')

    def test_base_bcd_complete_multiple(self):
        self.sendline('cd /usr')
        self.sendline('base')
        self.sendline('_base_bcd_complete "" "l"')
        self.sendline('echo "${#COMPREPLY[@]}"')
        self.expect_exact(b'\r\n2\r\n')
        self.sendline('echo "${COMPREPLY[@]}"')
        self.expect_exact(b'\r\nlib local\r\n')

    def test_source_base_bcd_complete_multiple(self):
        self.sendline('cd /usr')
        self.sendline('source base')
        self.sendline('_base_bcd_complete "" "l"')
        self.sendline('echo "${#COMPREPLY[@]}"')
        self.expect_exact(b'\r\n2\r\n')
        self.sendline('echo "${COMPREPLY[@]}"')
        self.expect_exact(b'\r\nlib local\r\n')

    def test_source_base_activate_bcd_complete_multiple(self):
        self.sendline('cd /usr')
        self.sendline('source base_activate')
        self.sendline('_base_bcd_complete "" "l"')
        self.sendline('echo "${#COMPREPLY[@]}"')
        self.expect_exact(b'\r\n2\r\n')
        self.sendline('echo "${COMPREPLY[@]}"')
        self.expect_exact(b'\r\nlib local\r\n')

    def test_base_bcd_complete_none(self):
        self.sendline('cd /usr')
        self.sendline('base')
        self.sendline('_base_bcd_complete "" "x"')
        self.sendline('echo "${#COMPREPLY[@]}"')
        self.expect_exact(b'\r\n0\r\n')

    def test_source_base_bcd_complete_none(self):
        self.sendline('cd /usr')
        self.sendline('source base')
        self.sendline('_base_bcd_complete "" "x"')
        self.sendline('echo "${#COMPREPLY[@]}"')
        self.expect_exact(b'\r\n0\r\n')

    def test_source_base_activate_bcd_complete_none(self):
        self.sendline('cd /usr')
        self.sendline('source base_activate')
        self.sendline('_base_bcd_complete "" "x"')
        self.sendline('echo "${#COMPREPLY[@]}"')
        self.expect_exact(b'\r\n0\r\n')

    # _base_deactivation_callback_register ###################################

    def test_base_deactivation_callback_register(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_deprj () { unset TEST_INT ; }')
                outfile.write('_base_deactivation_callback_register _deprj')
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('export TEST_INT=foo')
            self.sendline('echo "${TEST_INT}"')
            self.expect_exact(b'\r\nfoo\r\n')
            self.sendline('exit')
            self.assertUserPrompt()
            self.assertNotFound('TEST_INT')

    def test_source_base_deactivation_callback_register(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_deprj () { unset TEST_INT ; }')
                outfile.write('_base_deactivation_callback_register _deprj')
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('export TEST_INT=foo')
            self.sendline('echo "${TEST_INT}"')
            self.expect_exact(b'\r\nfoo\r\n')
            self.sendline('exit')
            self.assertUserPrompt()
            self.assertNotFound('TEST_INT')

    def test_source_base_activate_deactivation_callback_register(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_deprj () { unset TEST_INT ; }')
                outfile.write('_base_deactivation_callback_register _deprj')
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('export TEST_INT=foo')
            self.sendline('echo "${TEST_INT}"')
            self.expect_exact(b'\r\nfoo\r\n')
            self.sendline('base_deactivate')
            self.assertUserPrompt()
            self.assertNotFound('TEST_INT')

    # _base_var_set ##########################################################

    def test_base_var_set(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_var_set TEST_SET_VAR foo')
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${TEST_SET_VAR}"')
            self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_var_set(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_var_set TEST_SET_VAR foo')
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${TEST_SET_VAR}"')
            self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_activate_var_set(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_var_set TEST_SET_VAR foo')
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${TEST_SET_VAR}"')
            self.expect_exact(b'\r\nfoo\r\n')
            self.sendline('base_deactivate')
            self.assertUserPrompt()
            self.assertNotFound('TEST_SET_VAR')

    # _base_var_unset ########################################################

    def test_base_var_unset(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_var_unset TEST_UNSET_VAR')
            self.sendline('export TEST_UNSET_VAR=foo')
            self.sendline(f'cd {tempdir}')
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.assertNotFound('TEST_UNSET_VAR')
            self.sendline('exit')
            self.sendline('echo "${TEST_UNSET_VAR}"')
            self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_var_unset(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_var_unset TEST_UNSET_VAR')
            self.sendline('export TEST_UNSET_VAR=foo')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.assertNotFound('TEST_UNSET_VAR')
            self.sendline('exit')
            self.sendline('echo "${TEST_UNSET_VAR}"')
            self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_activate_var_unset(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_var_unset TEST_UNSET_VAR')
            self.sendline('export TEST_UNSET_VAR=foo')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.assertNotFound('TEST_UNSET_VAR')
            self.sendline('base_deactivate')
            self.sendline('echo "${TEST_UNSET_VAR}"')
            self.expect_exact(b'\r\nfoo\r\n')

    # _base_label_set ########################################################

    def test_base_label_set_auto(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set project')
            self.sendline(f'cd {tempdir}')
            self.sendline('base')
            self.assertBasePrompt(b'project', b'')

    def test_source_base_label_set_auto(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base')
            self.assertBasePrompt(b'project', b'')

    def test_source_base_activate_label_set_auto(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base_activate')
            self.assertBasePrompt(b'project', b'')

    def test_base_label_set_cli(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set project')
            self.sendline(f'cd {tempdir}')
            self.sendline('base cli')
            self.assertBasePrompt(b'project', b'')

    def test_source_base_label_set_cli(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base cli')
            self.assertBasePrompt(b'project', b'')

    def test_source_base_activate_label_set_cli(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base_activate cli')
            self.assertBasePrompt(b'project', b'')

    # _base_label_set_default ################################################

    def test_base_label_set_default_auto(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set_default project')
            self.sendline(f'cd {tempdir}')
            self.sendline('base')
            self.assertBasePrompt(b'project', b'')

    def test_source_base_label_set_default_auto(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set_default project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base')
            self.assertBasePrompt(b'project', b'')

    def test_source_base_activate_label_set_default_auto(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set_default project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base_activate')
            self.assertBasePrompt(b'project', b'')

    def test_base_label_set_default_cli(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set_default project')
            self.sendline(f'cd {tempdir}')
            self.sendline('base cli')
            self.assertBasePrompt(b'cli', b'')

    def test_source_base_label_set_default_cli(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set_default project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base cli')
            self.assertBasePrompt(b'cli', b'')

    def test_source_base_activate_label_set_default_cli(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with open(os.path.join(tempdir, '.base'), 'w') as outfile:
                outfile.write('_base_label_set_default project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base_activate cli')
            self.assertBasePrompt(b'cli', b'')

    # .base directory ########################################################

    def test_base_directory(self):
        with tempfile.TemporaryDirectory() as tempdir:
            basedir = os.path.join(tempdir, '.base')
            mkdir_p(basedir)
            with open(os.path.join(basedir, 'var'), 'w') as outfile:
                outfile.write('_base_var_set TEST_SET_VAR foo')
            with open(os.path.join(basedir, 'label'), 'w') as outfile:
                outfile.write('_base_label_set_default project')
            self.sendline(f'cd {tempdir}')
            self.sendline('base')
            self.assertBasePrompt(b'project', b'')
            self.sendline('echo "${TEST_SET_VAR}"')
            self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_directory(self):
        with tempfile.TemporaryDirectory() as tempdir:
            basedir = os.path.join(tempdir, '.base')
            mkdir_p(basedir)
            with open(os.path.join(basedir, 'var'), 'w') as outfile:
                outfile.write('_base_var_set TEST_SET_VAR foo')
            with open(os.path.join(basedir, 'label'), 'w') as outfile:
                outfile.write('_base_label_set_default project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base')
            self.assertBasePrompt(b'project', b'')
            self.sendline('echo "${TEST_SET_VAR}"')
            self.expect_exact(b'\r\nfoo\r\n')

    def test_source_base_activate_directory(self):
        with tempfile.TemporaryDirectory() as tempdir:
            basedir = os.path.join(tempdir, '.base')
            mkdir_p(basedir)
            with open(os.path.join(basedir, 'var'), 'w') as outfile:
                outfile.write('_base_var_set TEST_SET_VAR foo')
            with open(os.path.join(basedir, 'label'), 'w') as outfile:
                outfile.write('_base_label_set_default project')
            self.sendline(f'cd {tempdir}')
            self.sendline('source base_activate')
            self.assertBasePrompt(b'project', b'')
            self.sendline('echo "${TEST_SET_VAR}"')
            self.expect_exact(b'\r\nfoo\r\n')

    # python-virtualenv ######################################################

    def test_base_python_virtualenv_link(self):
        with temp_project_python(link='3.8.9') as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${PATH}"')
            self.expect_exact(
                b'\r\n' + tempdir.encode() + b'/virtualenv/bin:')

    def test_source_base_python_virtualenv_link(self):
        with temp_project_python(link='3.8.9') as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${PATH}"')
            self.expect_exact(
                b'\r\n' + tempdir.encode() + b'/virtualenv/bin:')

    def test_source_base_activate_python_virtualenv_link(self):
        with temp_project_python(link='3.8.9') as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${PATH}"')
            self.expect_exact(
                b'\r\n' + tempdir.encode() + b'/virtualenv/bin:')

    def test_base_python_virtualenv_single(self):
        with temp_project_python(versions=('3.8.9',)) as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${PATH}"')
            self.expect_exact(
                b'\r\n' + tempdir.encode() + b'/virtualenv-3.8.9/bin:')

    def test_source_base_python_virtualenv_single(self):
        with temp_project_python(versions=('3.8.9',)) as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${PATH}"')
            self.expect_exact(
                b'\r\n' + tempdir.encode() + b'/virtualenv-3.8.9/bin:')

    def test_source_base_activate_python_virtualenv_single(self):
        with temp_project_python(versions=('3.8.9',)) as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${PATH}"')
            self.expect_exact(
                b'\r\n' + tempdir.encode() + b'/virtualenv-3.8.9/bin:')

    def test_base_python_virtualenv_multiple(self):
        with temp_project_python() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.expect_exact(b'\r\nSelect Python virtual environment [1]:')
            self.sendline('2')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${PATH}"')
            self.expect_exact(
                b'\r\n' + tempdir.encode() + b'/virtualenv-3.8.9/bin:')

    def test_source_base_python_virtualenv_multiple(self):
        with temp_project_python() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.expect_exact(b'\r\nSelect Python virtual environment [1]:')
            self.sendline('2')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${PATH}"')
            self.expect_exact(
                b'\r\n' + tempdir.encode() + b'/virtualenv-3.8.9/bin:')

    def test_source_base_activate_python_virtualenv_multiple(self):
        with temp_project_python() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.expect_exact(b'\r\nSelect Python virtual environment [1]:')
            self.sendline('2')
            self.assertBasePrompt(tempdir_name, b'')
            self.sendline('echo "${PATH}"')
            self.expect_exact(
                b'\r\n' + tempdir.encode() + b'/virtualenv-3.8.9/bin:')

    def test_base_python_virtualenv_none(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.expect_exact(
                b'warning: no Python virtual environment loaded')
            self.assertBasePrompt(tempdir_name, b'')

    def test_source_base_python_virtualenv_none(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.expect_exact(
                b'warning: no Python virtual environment loaded')
            self.assertBasePrompt(tempdir_name, b'')

    def test_source_base_activate_python_virtualenv_none(self):
        with tempfile.TemporaryDirectory() as tempdir:
            tempdir_name = os.path.basename(tempdir).encode()
            os.symlink(
                '/usr/share/base/python-virtualenv.sh',
                os.path.join(tempdir, '.base'),
            )
            self.sendline(f'cd {tempdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.expect_exact(
                b'warning: no Python virtual environment loaded')
            self.assertBasePrompt(tempdir_name, b'')

    # go-ulo #################################################################

    def test_base_go_ulo_link(self):
        with temp_project_go(link='1.15.11') as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:{}:'.format(
                os.path.join(godir, 'bin'),
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())

    def test_source_base_go_ulo_link(self):
        with temp_project_go(link='1.15.11') as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:{}:'.format(
                os.path.join(godir, 'bin'),
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())

    def test_source_base_activate_go_ulo_link(self):
        with temp_project_go(link='1.15.11') as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:{}:'.format(
                os.path.join(godir, 'bin'),
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())

    def test_base_go_ulo_single(self):
        with temp_project_go(versions=('1.15.11',)) as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:{}:'.format(
                os.path.join(godir, 'bin'),
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())

    def test_source_base_go_ulo_single(self):
        with temp_project_go(versions=('1.15.11',)) as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:{}:'.format(
                os.path.join(godir, 'bin'),
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())

    def test_source_base_activate_go_ulo_single(self):
        with temp_project_go(versions=('1.15.11',)) as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:{}:'.format(
                os.path.join(godir, 'bin'),
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())

    def test_base_go_ulo_multiple(self):
        with temp_project_go() as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.expect_exact(b'\r\nSelect Go installation [1]:')
            self.sendline('2')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:{}:'.format(
                os.path.join(godir, 'bin'),
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())

    def test_source_base_go_ulo_multiple(self):
        with temp_project_go() as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.expect_exact(b'\r\nSelect Go installation [1]:')
            self.sendline('2')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:{}:'.format(
                os.path.join(godir, 'bin'),
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())

    def test_source_base_activate_go_ulo_multiple(self):
        with temp_project_go() as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.expect_exact(b'\r\nSelect Go installation [1]:')
            self.sendline('2')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:{}:'.format(
                os.path.join(godir, 'bin'),
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())

    def test_base_go_ulo_none(self):
        with temp_project_go(versions=()) as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.expect_exact(b'\r\nwarning: unable to set GOROOT')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.assertNotFound('GOROOT')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:'.format(
                os.path.join(godir, 'bin'),
            ).encode())

    def test_source_base_go_ulo_none(self):
        with temp_project_go(versions=()) as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.expect_exact(b'\r\nwarning: unable to set GOROOT')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.assertNotFound('GOROOT')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:'.format(
                os.path.join(godir, 'bin'),
            ).encode())

    def test_source_base_activate_go_ulo_none(self):
        with temp_project_go(versions=()) as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.expect_exact(b'\r\nwarning: unable to set GOROOT')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.assertNotFound('GOROOT')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:'.format(
                os.path.join(godir, 'bin'),
            ).encode())

    def test_base_go_ulo_no_ulo(self):
        with temp_project_go(versions=()) as projdir:
            sudo_rm_rf('/usr/local/opt')
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.expect_exact(b'\r\nwarning: /usr/local/opt not found')
            self.expect_exact(b'\r\nwarning: unable to set GOROOT')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.assertNotFound('GOROOT')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:'.format(
                os.path.join(godir, 'bin'),
            ).encode())

    def test_source_base_go_ulo_no_ulo(self):
        with temp_project_go(versions=()) as projdir:
            sudo_rm_rf('/usr/local/opt')
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base')
            self.expect_exact(b'\r\nwarning: /usr/local/opt not found')
            self.expect_exact(b'\r\nwarning: unable to set GOROOT')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.assertNotFound('GOROOT')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:'.format(
                os.path.join(godir, 'bin'),
            ).encode())

    def test_source_base_activate_go_ulo_no_ulo(self):
        with temp_project_go(versions=()) as projdir:
            sudo_rm_rf('/usr/local/opt')
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('source base_activate')
            self.expect_exact(b'\r\nwarning: /usr/local/opt not found')
            self.expect_exact(b'\r\nwarning: unable to set GOROOT')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.assertNotFound('GOROOT')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:'.format(
                os.path.join(godir, 'bin'),
            ).encode())

    def test_base_go_ulo_no_go_workspace(self):
        with temp_project_go(versions=('1.15.11',)):
            with tempfile.TemporaryDirectory() as tempdir:
                tempdir_name = os.path.basename(tempdir).encode()
                os.symlink(
                    '/usr/share/base/go-ulo.sh',
                    os.path.join(tempdir, '.base'),
                )
                self.sendline(f'cd {tempdir}')
                self.assertUserPrompt()
                self.sendline('base')
                self.expect_exact(b'\r\nwarning: not in a Go workspace')
                self.expect_exact(b'\r\nwarning: unable to set GOPATH')
                self.expect_exact(b'\r\nwarning: go command not found\r\n')
                self.assertBasePrompt(tempdir_name, b'')
                self.sendline('echo "${GOROOT}"')
                self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
                self.assertNotFound('GOPATH')
                self.sendline('echo "${PATH}"')
                self.expect_exact('\r\n{}:'.format(
                    '/usr/local/opt/go-1.15.11/bin',
                ).encode())

    def test_source_base_go_ulo_no_go_workspace(self):
        with temp_project_go(versions=('1.15.11',)):
            with tempfile.TemporaryDirectory() as tempdir:
                tempdir_name = os.path.basename(tempdir).encode()
                os.symlink(
                    '/usr/share/base/go-ulo.sh',
                    os.path.join(tempdir, '.base'),
                )
                self.sendline(f'cd {tempdir}')
                self.assertUserPrompt()
                self.sendline('source base')
                self.expect_exact(b'\r\nwarning: not in a Go workspace')
                self.expect_exact(b'\r\nwarning: unable to set GOPATH')
                self.expect_exact(b'\r\nwarning: go command not found\r\n')
                self.assertBasePrompt(tempdir_name, b'')
                self.sendline('echo "${GOROOT}"')
                self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
                self.assertNotFound('GOPATH')
                self.sendline('echo "${PATH}"')
                self.expect_exact('\r\n{}:'.format(
                    '/usr/local/opt/go-1.15.11/bin',
                ).encode())

    def test_source_base_activate_go_ulo_no_go_workspace(self):
        with temp_project_go(versions=('1.15.11',)):
            with tempfile.TemporaryDirectory() as tempdir:
                tempdir_name = os.path.basename(tempdir).encode()
                os.symlink(
                    '/usr/share/base/go-ulo.sh',
                    os.path.join(tempdir, '.base'),
                )
                self.sendline(f'cd {tempdir}')
                self.assertUserPrompt()
                self.sendline('source base_activate')
                self.expect_exact(b'\r\nwarning: not in a Go workspace')
                self.expect_exact(b'\r\nwarning: unable to set GOPATH')
                self.expect_exact(b'\r\nwarning: go command not found\r\n')
                self.assertBasePrompt(tempdir_name, b'')
                self.sendline('echo "${GOROOT}"')
                self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
                self.assertNotFound('GOPATH')
                self.sendline('echo "${PATH}"')
                self.expect_exact('\r\n{}:'.format(
                    '/usr/local/opt/go-1.15.11/bin',
                ).encode())

    def test_base_go_ulo_no_goroot_bin(self):
        with temp_project_go(versions=('1.15.11',)) as projdir:
            sudo_rm_rf('/usr/local/opt/go-1.15.11/bin')
            godir = os.path.dirname(os.path.dirname(projdir))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:'.format(
                os.path.join(godir, 'bin'),
            ).encode())

    def test_base_go_ulo_no_gopath_bin(self):
        with temp_project_go(versions=('1.15.11',)) as projdir:
            godir = os.path.dirname(os.path.dirname(projdir))
            os.rmdir(os.path.join(godir, 'bin'))
            projdir_name = os.path.basename(projdir).encode()
            os.symlink(
                '/usr/share/base/go-ulo.sh',
                os.path.join(projdir, '.base'),
            )
            self.sendline(f'cd {projdir}')
            self.assertUserPrompt()
            self.sendline('base')
            self.expect_exact(b'\r\nwarning: go command not found\r\n')
            self.assertBasePrompt(projdir_name, b'')
            self.sendline('echo "${GOROOT}"')
            self.expect_exact(b'\r\n/usr/local/opt/go-1.15.11\r\n')
            self.sendline('echo "${GOPATH}"')
            self.expect_exact(f'\r\n{godir}\r\n'.encode())
            self.sendline('echo "${PATH}"')
            self.expect_exact('\r\n{}:'.format(
                '/usr/local/opt/go-1.15.11/bin',
            ).encode())


##############################################################################
# main

if __name__ == '__main__':
    unittest.main()
