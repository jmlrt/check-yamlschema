import argparse
import json
import logging
import os
import re

import jsonschema
import requests
import yaml


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
                    "schema_url": schema_url,
                }
                yaml_documents.append(doc_dict)
    return yaml_documents


def download_schema(schema_url):
    response = requests.get(schema_url)
    response.raise_for_status()
    return response.json()


def validate_document(file, document, schema_url):
    if schema_url.startswith("http://") or schema_url.startswith("https://"):
        schema = download_schema(schema_url)
    else:
        current_dir = os.path.dirname(os.path.realpath(file))
        schema_path = os.path.join(current_dir, schema_url)

        with open(schema_path) as file:
            schema = json.load(file)
    jsonschema.validate(instance=document, schema=schema)


def main():
    logging.basicConfig(format="%(message)s")
    parser = argparse.ArgumentParser(
        description="Validate YAML document(s) against JSON schema."
    )
    parser.add_argument("files", nargs="+", help="Path to YAML files to validate")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    for file in args.files:
        yaml_documents = load_yaml_documents(file)
        logging.info("File %s: %s documents", file, len(yaml_documents))
        for index, doc in enumerate(yaml_documents):
            if doc["schema_url"] is not None:
                validate_document(file, doc["content"], doc["schema_url"])
                logging.info(
                    "- Document %s validated according to %s", index, doc["schema_url"]
                )
            else:
                logging.info(
                    "- Document %s has no JSON schema defined in comments", index
                )


if __name__ == "__main__":
    main()
