# Generate UML

Generate UML diagrams for Airbyte connection streams classes by comparing two git branches. This tool helps visualize the differences in your work across different branches.

## Features

- Compares connection streams classes between two branches.
- Generates UML diagrams highlighting added and removed methods and attributes.
- Uses Poetry for dependency management.

## Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)

## Installation

1. **Clone the repository:**

```bash
   git clone <repository_url>
   cd generate-uml
```

2. **Install dependencies using Poetry:**

```bash
   poetry install
```

## Usage

To run the tool and generate UML diagrams, use the following command:

```bash
   poetry run generate-uml --control-branch=master --target-branch=some-feature-branch --connector-name=connector-name
```

### Command-line Arguments

- `--control-branch`: The branch to compare from (e.g., `master`).
- `--target-branch`: The branch to compare to (e.g., `aldogonzalez8/source/stripe/upgrade-cdk3`).
- `--connector-name`: The name of the connector (e.g., `source-stripe`).
- `--show-only-differences`: Optional flag to show only the differences between branches in the UML diagram.

## Example
```bash
   poetry run generate-uml --control-branch=master --target-branch=aldogonzalez8/source/stripe/upgrade-cdk3 --connector-name=source-stripe
```
This will generate a UML diagram comparing the `streams.py` file in the `source-stripe` connector between the `master` branch and the `aldogonzalez8/source/stripe/upgrade-cdk3` branch. The generated UML diagram will be saved as `umls/class_uml_colored.png`.

## Future Improvements

- Dynamically resolve the location of `streams.py` for connectors.
- Integrate Airbyte protocols or source methods to determine stream class locations.

## Project Structure

```
generate-uml/
├── generate_uml/
│   ├── __init__.py
│   └── run.py
├── pyproject.toml
└── README.md
```


## Contributing

Feel free to submit issues, fork the repository, and make pull requests. Any contributions are welcome!

## License

This project is licensed under the MIT License.
