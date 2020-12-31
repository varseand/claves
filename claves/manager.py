import boto3
import json
import re
import pkg_resources

from os import path


class AWSManager(object):

    @staticmethod
    def list_regions():
        client = boto3.client("ec2", region_name="us-east-1")

        return [region["RegionName"]
                for region
                in client.describe_regions()["Regions"]]

    def __init__(self, region):
        self.__cloudformation = boto3.client("cloudformation", region_name=region)
        self.__ec2 = boto3.client("ec2", region_name=region)

    def create_stack(self, name, repository, keypair, instance_type, git_userdata):
        template_body = pkg_resources.resource_string(__name__, "data/enclave.yaml").decode("utf-8")

        parameters = [
            {
                "ParameterKey": "RepositoryName",
                "ParameterValue": repository["repositoryName"]
            }, {
                "ParameterKey": "RepositoryArn",
                "ParameterValue": repository["Arn"]
            }, {
                "ParameterKey": "RepositoryUrl",
                "ParameterValue": repository["cloneUrlHttp"]
            }, {
                "ParameterKey": "KeyName",
                "ParameterValue": keypair["KeyName"]
            }, {
                "ParameterKey": "InstanceType",
                "ParameterValue": instance_type,
            }, {
                "ParameterKey": "GitUsername",
                "ParameterValue": git_userdata["name"]
            }, {
                "ParameterKey": "GitEmail",
                "ParameterValue": git_userdata["email"]
            }
        ]
        capabilities = [
            "CAPABILITY_IAM"
        ]
        tags = [
            {
                "Key": "Repository",
                "Value": repository["repositoryName"]
            }, {
                "Key": "CreatedBy",
                "Value": "Claves"
            }
        ]

        return self.__cloudformation.create_stack(
            StackName=name,
            TemplateBody=template_body,
            Parameters=parameters,
            Capabilities=capabilities,
            Tags=tags)

    def delete_stack(self, name):
        return self.__cloudformation.delete_stack(
            StackName=name
        )

    def list_enclaves(self, name_pattern=None, repository_pattern=None, verbose=False):

        def is_claves_stack(stack):
            return {"Key": "CreatedBy", "Value": "Claves"} in stack["Tags"]

        def by_name(stack):
            return name_pattern is None or re.match(name_pattern, stack["StackName"])

        def by_repository(stack):

            if repository_pattern is None:
                return True

            return any(True for parameter
                       in stack["Parameters"]
                       if parameter.get("ParameterKey") == "RepositoryName" and re.match(repository_pattern, parameter.get("ParameterValue", "")))

        def transform_stack(stack):
            del stack["Capabilities"]
            del stack["Description"]
            del stack["DisableRollback"]
            del stack["DriftInformation"]
            del stack["NotificationARNs"]
            del stack["RollbackConfiguration"]

            if not verbose:
                del stack["Tags"]
                del stack["StackId"]

            if "Outputs" in stack:

                basic_outputs = ("PublicDNS", )
                if not verbose:
                    stack["Outputs"] = list(output for output
                                            in stack["Outputs"]
                                            if output["OutputKey"] in basic_outputs)

                for output in stack["Outputs"]:
                    del output["Description"]

            basic_parameters = ("RepositoryUrl", )
            if not verbose:
                stack["Parameters"] = list(parameter for parameter
                                           in stack["Parameters"]
                                           if parameter["ParameterKey"] in basic_parameters)

            return stack

        summaries = self.__cloudformation.describe_stacks()["Stacks"]
        summaries = filter(is_claves_stack, summaries)
        summaries = filter(by_name, summaries)
        summaries = filter(by_repository, summaries)
        summaries = map(transform_stack, summaries)

        return list(summaries)

    def get_keypair(self, name, region=None):
        response = self.__ec2.describe_key_pairs(KeyNames=[name, ])
        return response["KeyPairs"][0]
