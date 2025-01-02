# check-yamlschema

A CLI and pre-commit hook for jsonschema validation in YAML files with multiple documents

Parse multi-documents YAML files, look for [inline schema comments][], and validate the documents according to their schema.

The inline schema comments should use the following format:

```yaml
# yaml-language-server: $schema=<schema_url>
food: # Some YAML document
  - vegetables: tomatoes
  - fruits:
      citrics: oranges
      tropical: bananas
      nuts: peanuts
      sweets: raisins
---
# yaml-language-server: $schema=<another_schema_url
name: Martin Devloper # Some other YAML document
age: 26
hobbies:
  - painting
  - playing_music
  - cooking
programming_languages:
  java: Intermediate
  python: Advanced
  javascript: Beginner
favorite_food:
  - vegetables: tomatoes
  - fruits:
      citrics: oranges
      tropical: bananas
      nuts: peanuts
      sweets: raisins
```

## CLI usage

- Install it with `pip install check-yamlschema`
- Run it with some YAML files in parameters: `check-yamlschema file1.yaml file2.yaml ...`

## Pre-commit usage

Add this to your `.pre-commit-config.yaml`:

```yaml
  - repo: https://github.com/jmlrt/check-yamlschema
    rev: v0.0.5
    hooks:
      - id: check-yamlschema
```

[inline schema comments]: https://github.com/redhat-developer/yaml-language-server/blob/762209ccdfca713d203ead757698a47ad3cabf50/README.md#using-inlined-schema
