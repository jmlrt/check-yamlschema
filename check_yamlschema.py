import argparse
import json
import logging
import os
import re

import jsonschema
import requests
import yaml


def is_remote_schema(schema_url):
    return schema_url.startswith("http://") or schema_url.startswith("https://")


def get_absolute_path(file, schema_path):
    if not schema_path or is_remote_schema(schema_path):
        return schema_path

    current_dir = os.path.dirname(os.path.realpath(file))
    schema_path = os.path.join(current_dir, schema_path)
    abs_path = os.path.abspath(schema_path)
    return abs_path


def get_validator(with_k8s_extension):
    basic_validator = jsonschema.validators.Draft202012Validator

    if not with_k8s_extension:
        return basic_validator

    basic_additional_props_validator = basic_validator.VALIDATORS[
        "additionalProperties"
    ]

    def additional_props_hook(validator, value, instance, schema):
        if "x-kubernetes-preserve-unknown-fields" in schema:
            if type(schema["properties"]) is dict:
                for prop in list(instance.keys()):
                    if prop not in schema["properties"]:
                        del instance[prop]

        return basic_additional_props_validator(validator, value, instance, schema)

    custom_validator = jsonschema.validators.extend(
        basic_validator, validators={"additionalProperties": additional_props_hook}
    )

    return custom_validator


def load_yaml_documents(file_path):
    with open(file_path) as file:
        content = file.read()
        documents = content.split("---\n")
        yaml_documents = []
        for doc in documents:
            if doc.strip() != "":
                comment = None
                schema_url = None
                for line in doc.split("\n"):
                    if line.startswith("# yaml-language-server"):
                        comment = line
                        match = re.match(
                            r"# yaml-language-server: \$schema=(.*)$",
                            comment,
                            re.MULTILINE,
                        )
                        if match:
                            schema_url = match.group(1)
                        break
                doc_dict = {
                    "content": yaml.safe_load(doc),
                    "comment": comment,
                    "schema_url": get_absolute_path(file_path, schema_url),
                }
                yaml_documents.append(doc_dict)

    return yaml_documents


def download_schema(schema_url):
    response = requests.get(schema_url)
    response.raise_for_status()
    return response.json()


def validate_document(file, document, schema_url, validator):
    if is_remote_schema(schema_url):
        schema = download_schema(schema_url)
    else:
        with open(schema_url) as file:
            schema = json.load(file)

    validator(schema).validate(document)


def main():
    logging.basicConfig(format="%(message)s")
    parser = argparse.ArgumentParser(
        description="Validate YAML document(s) against JSON schema."
    )
    parser.add_argument("files", nargs="+", help="Path to YAML files to validate")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--k8s", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.ERROR)

    validator = get_validator(args.k8s)
    fails_count = 0

    for file in args.files:
        yaml_documents = load_yaml_documents(file)

        for index, doc in enumerate(yaml_documents):
            if doc["schema_url"] is not None:
                try:
                    validate_document(
                        file, doc["content"], doc["schema_url"], validator
                    )
                    logging.debug(
                        f"{file} document {index}: validated according to {doc["schema_url"]}"
                    )
                except jsonschema.exceptions.ValidationError as exception:
                    logging.error(
                        f"{file} document {index}: validation failed according to {doc["schema_url"]}:\n"
                        f"{exception.message}"
                    )
                    logging.debug(exception, stack_info=True)
                    fails_count += 1
                except Exception as exception:
                    logging.error(
                        f"{file} document {index}: validation failed:\n  {exception}"
                    )
                    fails_count += 1
            else:
                logging.debug(f"{file}: no JSON schema defined in comments")

    return fails_count


if __name__ == "__main__":
    main()
