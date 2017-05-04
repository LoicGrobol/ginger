'''Release a new version.

Usage:
  release (major|minor|patch|explicit <version>) [--name <name>]

Options:
  --name, -n <name>  A (code?)name for the release
'''

__version__ = 'release 0.0.0'


import sys
import json
import pathlib
import re
import datetime
import subprocess
import tempfile

import typing as ty

from collections import OrderedDict, defaultdict

from docopt import docopt
import appdirs
import requests

CONFIG_PATH = pathlib.Path(appdirs.user_config_dir('diroll', False, __version__.split(' ')[-1]))/'config.json'


class Version:
    '''Semver versions.'''
    def __init__(self, major: int, minor: int, patch: int):
        self.major = major
        self.minor = minor
        self.patch = patch

    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        return cls(*(int(l) for l in version_str.split('.')))

    def __str__(self):
        return '{major}.{minor}.{patch}'.format(major=self.major,
                                                minor=self.minor,
                                                patch=self.patch)


def main_entry_point(argv=sys.argv[1:]):
    arguments = docopt(__doc__, version=__version__, argv=argv)

    if arguments["--name"] is None:
        arguments["--name"] = '(Anonymous release)'

    package_dir = pathlib.Path(__file__).resolve().parents[1]

    if git_dirty(package_dir):
        raise Exception('Uncommitted changes in {package_dir}.'.format(package_dir))

    # Get the current version from `package.json`
    package_data = get_package_data(package_dir)

    package_current_version = Version.from_string(package_data["version"])

    # Increment the appropriate level
    if arguments['major']:
        package_new_version = Version(package_current_version.major+1, 0, 0)
    elif arguments['minor']:
        package_new_version = Version(package_current_version.major,
                                      package_current_version.minor+1, 0)
    elif arguments['patch']:
        package_new_version = Version(package_current_version.major,
                                      package_current_version.minor,
                                      package_current_version.patch+1)
    else:
        package_new_version = Version.from_string(arguments['<version>'])

    # Set the version in `package.json`
    package_data["version"] = str(package_new_version)
    set_package_data(package_dir, package_data)

    # Set the version in the main script
    main_path = package_dir/'ginger.py'
    main_str = main_path.read_text()
    new_main_str = re.sub(r"(__version__ = (['\"]).*).+\2".format(package_current_version),
                          r'\g<1>{}\2'.format(package_new_version),
                          main_str)
    main_path.write_text(new_main_str)

    # Release in change log
    changelog_path = package_dir/'CHANGELOG.md'
    changelog_str = changelog_path.read_text()

    new_changelog_str = re.sub((
            r'## \[Unreleased\]' '\n'
            r'\[Unreleased\]: (?P<url>.*?)/compare/.+HEAD').format(package_current_version), (
            '## [Unreleased]\n'
            r'[Unreleased]: \g<url>/compare/v{0}...HEAD' '\n\n'
            r'## [{0}] - {2}' '\n'
            r'[{0}]: \g<url>/compare/v{1}...{0}').format(package_new_version,
                                                         package_current_version,
                                                         datetime.date.today().isoformat()),
            changelog_str)

    changelog_path.write_text(new_changelog_str)

    # Commit and push the changes in git
    # Extract the change list from the change log
    changes = log_from_changes(changes_from_log(changelog_str))

    repo_url = package_data["url"]
    changes = ('# {}\n'.format(package_new_version) +
               changes +
               ('\n\n' 'See the full diff at'
                '<{repo_url}/compare/{package_current_version}...{package_new_version}>' '\n\n'
                'See [the change log](CHANGELOG.md) for more informations about past releases.'
                ).format(repo_url=repo_url,
                         package_new_version=package_new_version,
                         package_current_version=package_current_version))

    git_dir = package_dir/'.git'
    git_options = ['git', '--git-dir', str(git_dir),  '--work-tree', str(package_dir)]
    subprocess.run([*git_options, 'add',
                    str(package_dir/'package.json'),
                    str(changelog_path),
                    str(main_path)], check=True)
    subprocess.run([*git_options, 'commit', '-m', 'Release v{}'.format(package_new_version)])

    tag_name = 'v{}'.format(package_new_version)
    with tempfile.NamedTemporaryFile(mode='w') as tag_message_file:
        tag_message_file.write(changes.replace('###', '##'))
        tag_message_file.flush()

        subprocess.run([*git_options, 'tag',
                        '-F', tag_message_file.name,
                        '--cleanup=verbatim',
                        tag_name], check=True)
        subprocess.run([*git_options, 'push',
                        '--follow-tags', '--atomic'], check=True)

    release_github(repo_url,
                   tag_name, '{tag_name} {release_name}'.format(tag_name=tag_name,
                                                                release_name=arguments['--name']),
                   changes=changes)


def changes_from_log(changelog: str, *,
                     source_version: str = None,
                     dest_version: str = 'Unreleased') -> ty.Dict:
    # Iter over all non-blank lines in `changelog`
    lines_iter = (l for l in changelog.splitlines() if not l.isspace())
    current_line = next(lines_iter)

    # Search for the start of the version range
    start_re = re.compile(r'##.*{dest_version}'.format(
        dest_version=re.escape(dest_version)))
    while not start_re.match(current_line):
        current_line = next(lines_iter)
    current_line = next(lines_iter)

    # Now read the changes
    res = defaultdict(list)
    current_section = None
    if source_version is None:
        end_re = re.compile(r'##[^#]')
    else:
        end_re = re.compile(r'##.*{source_version}'.format(
            dest_version=re.escape(source_version)))
    section_re = re.compile(r'###\s*(?P<name>.*)')
    item_re = re.compile(r'\s+\-\s*(?P<content>.*)')
    while not end_re.match(current_line):
        try:
            current_line = next(lines_iter)
        except StopIteration:
            break
        section = section_re.match(current_line)
        if section:
            current_section = section.group('name')
            continue
        item = item_re.match(current_line)
        if item:
            res[current_section].append(item.group('content'))
            continue
    return res


def log_from_changes(changes: ty.Dict) -> str:
    halfway = {title: '\n'.join('  - {}'.format(item) for item in content)
               for title, content in changes.items()}
    res = '\n\n'.join('### {title}\n{content}'.format(title=title, content=content)
                      for title, content in halfway.items())
    return res


def set_package_data(package_dir: pathlib.Path, data: ty.Dict):
    package_data_path = package_dir/'package.json'
    with package_data_path.open('w') as package_stream:
        json.dump(data, package_stream, indent=4, ensure_ascii=False)


def get_package_data(package_dir: pathlib.Path):
    package_data_path = package_dir/'package.json'
    package_data_str = package_data_path.read_text()
    return json.loads(package_data_str, object_pairs_hook=OrderedDict)


def git_dirty(package_dir):
    git_dir = package_dir/'.git'
    fail = subprocess.run(['git', '--git-dir', str(git_dir),  '--work-tree', str(package_dir),
                           'diff-index', '--quiet', '--cached',
                           'HEAD']).returncode
    return fail


def get_config(config_path=CONFIG_PATH) -> ty.Dict:
    try:
        with config_path.open() as config_stream:
            config_dict = json.load(config_stream)
    except FileNotFoundError:
        config_dict = {"access": {}}
        set_config(config_dict, config_path)
    return config_dict


def set_config(config_dict: ty.Dict, config_path=CONFIG_PATH):
    if not config_path.exists():
        config_path.parent.mkdir(parents=True)

    with config_path.open('w') as config_stream:
        json.dump(config_dict, config_stream)


def get_github_token(url):
    config = get_config()
    try:
        username, token = config["access"][url]
    except KeyError:
        print("No access for {url} yet.".format(url=url))
        username = input("User name for {url}: ".format(url=url))
        token = input("Token for {url} (get one from https://github.com/settings/tokens/new): ".format(url=url))
        config["access"][url] = (username, token)
        set_config(config)
    return username, token


def release_github(repo_url, tag, name, changes):
    auth = get_github_token(repo_url)
    url = repo_url.replace('github.com', 'api.github.com/repos') + '/releases'
    r = requests.post(url, auth=auth, data=json.dumps({
        "tag_name": tag,
        "name": name,
        "body": changes
    }))


if __name__ == '__main__':
    # print(changes_from_log(open('CHANGELOG.md').read()))
    main_entry_point()
