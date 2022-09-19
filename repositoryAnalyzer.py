"""Git repository cyclomatic complexity analyzer exports data into a JSON format
"""

import json
from itertools import groupby
from os import path

import matplotlib.pyplot as plt
from pydriller import Repository

# Path to the repository (absolute or relative path)
REPO_PATH: str = "/home/user/repository"

# List of file extensions that are analyzed
FILTER_FILE_TYPES: list = ['.cpp', '.c']


class ParsedCommit:
    def __init__(self,
                 commit_hash: str, commit_date: str, user_name: str,
                 user_email: str, file_name: str, complexity: int,
                 avg_complexity: float):

        self.hash: str = commit_hash
        self.date: str = commit_date
        self.user: str = user_name
        self.email: str = user_email
        self.file_name: str = file_name
        self.ccn: int = complexity
        # self.avgCCN: str = "%.3f" % avg_complexity
        self.avgCCN: float = avg_complexity

    def __repr__(self) -> str:
        return f"{self.hash}, {self.date}, {self.user}, {self.email}, {self.file_name}, {self.ccn}, {self.avgCCN}"


def parse_commits(repo_path: str, filter_by_extension: list[str]) -> list[ParsedCommit]:
    """Extracts information form the commits on the repository path

    Args:
        repo_path (str): Repository path, local or remote
        filter_by_extension (list[str]): list of extensions to filter files by, ex. .c, .cpp, .py

    Returns:
        list[ParsedCommit]: List of LinearHistory objects containing parsed data
    """
    linear_history_list: list = []

    repo = Repository(repo_path)
    list_of_commits = repo.traverse_commits()

    print(" * Parsing commits")
    for commit in list_of_commits:
        date = str(commit.author_date)
        hash = str(commit.hash)
        user = str(commit.author.name)
        email = str(commit.author.email)

        print(f"\tcommit: {date} by {user} ({email}) | {commit.branches}")
        if commit.modified_files is None:
            print(f"*** MERGE {hash} @ {date} by {user} ({email}) ***")

        for file in commit.modified_files:
            # Skip if file has no complexity (zero is still some complexity)
            if file.complexity is None:
                continue

            file_name, file_ext = path.splitext(file.filename)
            if file_ext in filter_by_extension:

                complexity = file.complexity
                num_of_methods: int = len(file._function_list)
                avg_complexity: float = 0

                if num_of_methods > 0:
                    avg_complexity = complexity / num_of_methods
                else:
                    avg_complexity = 0

                linear_history_list.append(
                    ParsedCommit(hash, date, user, email, file_name, complexity, avg_complexity))

    return linear_history_list


def get_list_of_files(data: list[ParsedCommit]) -> list[str]:
    """Gets a list of files from parsed commit data

    Args:
        data (list[ParsedCommit]): List of ParsedCommit objects containing parsed data

    Returns:
        list[str]: List of file names
    """
    list_of_files = list()

    for item in data:
        if item.file_name not in list_of_files:
            list_of_files.append(item.file_name)

    return sorted(list_of_files)


if __name__ == '__main__':

    print("::: [ Git Repository Analyzer ] :::")

    parsed_commit = parse_commits(REPO_PATH, FILTER_FILE_TYPES)

    file_list = get_list_of_files(parsed_commit)

    # Sort items by file
    parsed_commit.sort(key=lambda x: x.file_name)
    # Group items by file
    groupedByFile = [list(result) for key, result in groupby(
        parsed_commit, key=lambda x: x.file_name)]

    # To change a structure of JSON data change this part
    data = {}
    for group in groupedByFile:
        group_name = group[0].file_name
        item_data = dict()
        for item in group:
            item_data[item.date] = {
                'avg_ccn': item.avgCCN, 'abs_ccn': item.ccn}
        data[group_name] = {'timestamp': item_data}

    json_object = json.dumps(data, indent=2)
    with open("out.json", "w", encoding="utf-8") as f:
        f.write(json_object)
