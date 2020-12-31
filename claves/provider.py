import boto3
import re


class CodeCommitProvider(object):

    def __init__(self, region=None):
        self.__client = boto3.client("codecommit", region_name=region)

    def list_repositories(self, name_pattern=None):

        def by_name(repository):
            return name_pattern is None or re.match(name_pattern, repository["repositoryName"])

        response = self.__client.list_repositories()
        repositories = response["repositories"]
        repositories = filter(by_name, repositories)

        return list(repositories)

    def get_repository(self, repository_name):
        response = self.__client.get_repository(repositoryName=repository_name)
        return response["repositoryMetadata"]
