import argparse
import yaml
import subprocess
import os
import sys
import re

from botocore.exceptions import ClientError, NoRegionError
from .manager import AWSManager
from .provider import CodeCommitProvider
from .utils import *


class ApplicationError(RuntimeError):

    def __init__(self, message, code):
        super().__init__(message, code)


def run_create(parsed, aws_manager, codecommit):

    if not parsed.keypair:
        raise ApplicationError("You must specify a key pair. You can also configure your key pair by exporting CLAVES_KEYPAIR.", 1001)

    if not parsed.repository:
        raise ApplicationError("You must specify a repository.", 1002)

    if parsed.instance_family not in ("t3", "t4g"):
        raise ApplicationError("EC2 family %r is not supported." % (parsed.instance_family, ), 1008)

    if parsed.instance_size not in ("nano", "micro", "small", "medium"):
        raise ApplicationError("EC2 size %r is not supported." % (parsed.instance_size, ), 1009)

    instance_type = f"{parsed.instance_family}.{parsed.instance_size}"

    try:
        keypair = aws_manager.get_keypair(parsed.keypair)

    except ClientError as error:
        if error.response["Error"]["Code"] != "InvalidKeyPair.NotFound":
            raise
        raise ApplicationError("The key pair %r does not exist" % (parsed.keypair, ), 1003)

    try:
        repository = codecommit.get_repository(parsed.repository)

    except ClientError as error:
        if error.response["Error"]["Code"] != "RepositoryDoesNotExistException":
            raise
        raise ApplicationError("Repository %r does not exist." % (parsed.repository, ), 1004)

    enclaves = aws_manager.list_enclaves(verbose=True)
    needle = {"ParameterKey": "RepositoryArn", "ParameterValue": repository["Arn"]}
    reserved_names = list(enclave["StackName"] for enclave in enclaves)

    if any(True for enclave in enclaves if needle in enclave["Parameters"]) and not parsed.force:
        raise ApplicationError("Code enclave for repository %r already exists (use --force to create anyway)." % (repository['repositoryName'], ), 1005)

    if parsed.name is None:
        parsed.name = get_next_free_name_like(f"CodeEnclaveFor{repository['repositoryName']}", reserved_names)
        if parsed.name is None:
            raise ApplicationError("Too much code enclaves for repository %r" % (repository['repositoryName'], ), 1006)

    elif parsed.name in reserved_names:
        raise ApplicationError("Code enclave with the name %r already exists." % (parsed.name, ), 1007)

    aws_manager.create_stack(
        parsed.name,
        repository,
        keypair,
        instance_type,
        {"name": parsed.username, "email": parsed.email})

    enclaves = aws_manager.list_enclaves(name_pattern=as_literal(parsed.name),
                                         verbose=True)
    print_yaml(enclaves)


def run_delete(parsed, aws_manager):

    if not parsed.name and not parsed.repository:
        raise ApplicationError("You must specify either --name or --repository.", 2001)

    enclaves = aws_manager.list_enclaves(name_pattern=as_pattern(parsed.name),
                                         repository_pattern=as_pattern(parsed.repository),
                                         verbose=parsed.verbose)
    enclaves_count = len(enclaves)
    if enclaves_count == 0:
        raise ApplicationError("No code enclaves to delete.", 0)

    try:
        print_text("The following code enclave%s will be deleted:" % (
            "s" if enclaves_count > 1 else "", ))
        print_yaml(enclaves)

        if parsed.yes or ask_for_confirmation("Do you want delete %s?" % (
            f"these {enclaves_count} code enclaves" if enclaves_count > 1 else "this code enclave", )
        ):
            if parsed.yes:
                print_text("Not asking for confirmation as --yes were used.")

            for enclave in enclaves:
                aws_manager.delete_stack(enclave["StackName"])

            print_text("Deletion of %s was initiated." % (
                f"{enclaves_count} code enclaves" if enclaves_count > 1 else "code enclave", ))
        else:
            print_text("No code enclaves deleted.")

    except StopIteration:
        pass


def run_list(parsed, aws_manager):

    enclaves = aws_manager.list_enclaves(name_pattern=as_pattern(parsed.name),
                                         repository_pattern=as_pattern(parsed.repository),
                                         verbose=parsed.verbose)
    if len(enclaves) == 0:
        raise ApplicationError("No code enclaves to list.", 0)

    print_yaml(enclaves)


def run_repositories(parsed, codecommit):

    repositories = codecommit.list_repositories(name_pattern=as_pattern(parsed.name))
    if len(repositories) == 0:
        raise ApplicationError("No repositories to list.", 0)

    print_yaml(repositories)


def run(args):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create")
    delete_parser = subparsers.add_parser("delete")
    list_parser = subparsers.add_parser("list")
    repositories_parser = subparsers.add_parser("repositories")

    create_parser.add_argument(
        "-n", "--name",
        dest="name",
        help="Name of the new enclave.",
        default=None
    )
    create_parser.add_argument(
        "-r", "--repository",
        dest="repository",
        help="Name of the repository to be cloned in the enclave."
    )
    create_parser.add_argument(
        "-u", "--git-username",
        dest="username",
        help="Git username to be used by the enclave.",
        default=subprocess.check_output(
            "git config --get user.name", shell=True).decode("utf-8").rstrip()
    )
    create_parser.add_argument(
        "-e", "--git-email",
        dest="email",
        help="Git email to be used by the enclave.",
        default=subprocess.check_output(
            "git config --get user.email", shell=True).decode("utf-8").rstrip()
    )
    create_parser.add_argument(
        "-k", "--keypair",
        dest="keypair",
        help="KeyPair to be used with the new enclave.",
        default=os.getenv("CLAVES_KEYPAIR", "")
    )
    create_parser.add_argument(
        "-f", "--force",
        dest="force",
        help="Create a new code enclave even if it already exists for given repository.",
        default=False,
        action="store_true"
    )
    create_parser.add_argument(
        "--instance-family",
        dest="instance_family",
        help="AWS EC2 instance family to use.",
        default="t3"
    )
    create_parser.add_argument(
        "--instance-size",
        dest="instance_size",
        help="AWS EC2 instance size to use.",
        default="nano"
    )
    create_parser.add_argument(
        "--region",
        dest="region",
        help="Create code enclaves and search for repositories in this region.",
        default=None
    )
    create_parser.add_argument(
        "--instance-region",
        dest="instance_region",
        help="Create code enclaves in this region (overrides --region).",
        default=None
    )
    create_parser.add_argument(
        "--repository-region",
        dest="repository_region",
        help="Search for repositories in this region (overrides --region).",
        default=None
    )

    delete_parser.add_argument(
        "-n", "--name",
        dest="name",
        help="Delete code enclaves matching a wildcard name."
    )
    delete_parser.add_argument(
        "-r", "--repository",
        dest="repository",
        help="Delete code enclaves matching a wildcard repository."
    )
    delete_parser.add_argument(
        "-y", "--yes",
        dest="yes",
        help="Do not ask for confirmation.",
        default=False,
        action="store_true"
    )
    delete_parser.add_argument(
        "-v", "--verbose",
        dest="verbose",
        help="Show more details.",
        default=False,
        action="store_true"
    )
    delete_parser.add_argument(
        "--region",
        dest="region",
        help="Delete code enclaves in this region.",
        default=None
    )

    list_parser.add_argument(
        "-n", "--name",
        dest="name",
        help="List code enclaves matching a wildcard name."
    )
    list_parser.add_argument(
        "-r", "--repository",
        dest="repository",
        help="List code enclaves matching a wildcard repository."
    )
    list_parser.add_argument(
        "-v", "--verbose",
        dest="verbose",
        help="Show more details.",
        default=False,
        action="store_true"
    )
    list_parser.add_argument(
        "--region",
        dest="region",
        help="List code enclaves in this region.",
        default=None
    )

    repositories_parser.add_argument(
        "-n", "--name",
        dest="name",
        help="List repositories matching a wildcard name."
    )
    repositories_parser.add_argument(
        "--region",
        dest="region",
        help="Search for repositories in this region.",
        default=None
    )

    parsed = parser.parse_args(args)

    for attribute in ("instance_region", "repository_region", "region"):
        if not hasattr(parsed, attribute):
            setattr(parsed, attribute, None)

    if parsed.region:
        if parsed.instance_region is None:
            parsed.instance_region = parsed.region

        if parsed.repository_region is None:
            parsed.repository_region = parsed.region

    allowed_regions = AWSManager.list_regions()
    try:
        if parsed.instance_region is not None and parsed.instance_region not in allowed_regions:
            raise ApplicationError("Invalid region: %r." % (parsed.instance_region, ), 1)

        aws_manager = AWSManager(parsed.instance_region)

        if parsed.repository_region is not None and parsed.repository_region not in allowed_regions:
            raise ApplicationError("Invalid region: %r." % (parsed.repository_region, ), 1)

        codecommit = CodeCommitProvider(parsed.repository_region)

        if parsed.command == "create":
            run_create(parsed, aws_manager, codecommit)
        elif parsed.command == "delete":
            run_delete(parsed, aws_manager)
        elif parsed.command == "list":
            run_list(parsed, aws_manager)
        elif parsed.command == "repositories":
            run_repositories(parsed, codecommit)

        else:  # none or invalid command
            parser.print_help()

    except NoRegionError as error:
        print_text("You must specify a region. You can also configure your region by running \"aws configure\".", 2)

    except ApplicationError as error:
        print_text(*error.args)
