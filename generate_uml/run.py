import ast
import os
import argparse

from git import Repo
from graphviz import Digraph


def parse_class(filename):
    with open(filename, "r") as file:
        tree = ast.parse(file.read())
    class_info = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            attributes = []
            for n in node.body:
                if isinstance(n, ast.Assign):
                    for target in n.targets:
                        if isinstance(target, ast.Name):
                            attributes.append(target.id)
            bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
            class_info[node.name] = {"methods": methods, "attributes": attributes, "bases": bases}
    return class_info


def combine_class_info(info1, info2):
    combined_info = {}
    all_classes = set(info1.keys()).union(set(info2.keys()))
    for class_name in all_classes:
        combined_info[class_name] = {
            "methods": list(set(info1.get(class_name, {}).get("methods", [])).union(
                set(info2.get(class_name, {}).get("methods", [])))),
            "attributes": list(
                set(info1.get(class_name, {}).get("attributes", [])).union(
                    set(info2.get(class_name, {}).get("attributes", [])))
            ),
            "bases": list(
                set(info1.get(class_name, {}).get("bases", [])).union(set(info2.get(class_name, {}).get("bases", [])))),
        }
    return combined_info


def compare_classes(class1_info, class2_info):
    differences = {}
    for class_name in set(class1_info.keys()).union(class2_info.keys()):
        methods_removed = list(
            set(class1_info.get(class_name, {}).get("methods", [])) - set(
                class2_info.get(class_name, {}).get("methods", []))
        )
        methods_added = list(
            set(class2_info.get(class_name, {}).get("methods", [])) - set(
                class1_info.get(class_name, {}).get("methods", []))
        )
        attributes_removed = list(
            set(class1_info.get(class_name, {}).get("attributes", [])) - set(
                class2_info.get(class_name, {}).get("attributes", []))
        )
        attributes_added = list(
            set(class2_info.get(class_name, {}).get("attributes", [])) - set(
                class1_info.get(class_name, {}).get("attributes", []))
        )
        differences[class_name] = {
            "methods_removed": methods_removed,
            "attributes_removed": attributes_removed,
            "methods_added": methods_added,
            "attributes_added": attributes_added,
        }
    return differences


def class_info_to_uml(class_info, differences=None, graph=None, show_only_differences=False):
    if graph is None:
        graph = Digraph(format="png")
        graph.attr("node", shape="plaintext")

    for class_name, info in class_info.items():
        attributes = set(info["attributes"])
        methods = set(info["methods"])

        include_methods_and_attributes = True
        reduced_view_row = ""
        if differences and class_name in differences:
            diff = differences[class_name]
            attributes_removed = {f"- <s>{attr}</s>" for attr in diff["attributes_removed"]}
            attributes_added = {f"+ {attr}" for attr in diff["attributes_added"]}
            methods_removed = {f"- <s>{method}</s>" for method in diff["methods_removed"]}
            methods_added = {f"+ {method}" for method in diff["methods_added"]}

            # Ensure no duplicates
            attributes = (attributes - set(diff["attributes_removed"])) | attributes_removed
            methods = (methods - set(diff["methods_removed"])) | methods_removed
            attributes = (attributes - set(diff["attributes_added"])) | attributes_added
            methods = (methods - set(diff["methods_added"])) | methods_added

            if show_only_differences:
                include_methods_and_attributes = bool(
                    attributes_removed or attributes_added or methods_removed or methods_added)
                if not include_methods_and_attributes:
                    reduced_view_row = '<TR><TD BGCOLOR="#FFA07A">Reduced View - No changes were detected</TD></TR>'

        attributes_rows = "".join(
            f'<TR><TD ALIGN="LEFT" BGCOLOR="#ffdce0">{attr}</TD></TR>'
            if "<s>" in attr
            else f'<TR><TD ALIGN="LEFT" BGCOLOR="#e6ffed">{attr}</TD></TR>'
            if "+" in attr
            else f'<TR><TD ALIGN="LEFT" BGCOLOR="white">{attr}</TD></TR>'
            for attr in attributes
        )
        methods_rows = "".join(
            f'<TR><TD ALIGN="LEFT" BGCOLOR="#ffdce0">{method}</TD></TR>'
            if "<s>" in method
            else f'<TR><TD ALIGN="LEFT" BGCOLOR="#e6ffed">{method}</TD></TR>'
            if "+" in method
            else f'<TR><TD ALIGN="LEFT" BGCOLOR="white">{method}</TD></TR>'
            for method in methods
        )

        attributes_title_row = '<TR><TD BGCOLOR="lightsteelblue">Attributes:</TD></TR>' if attributes else ""
        methods_title_row = '<TR><TD BGCOLOR="lightcyan">Methods:</TD></TR>' if methods else ""

        label = f"""<
        <TABLE BORDER="1" CELLBORDER="1" CELLSPACING="0">
            <TR><TD BGCOLOR="lightblue">{class_name}</TD></TR>
            {attributes_title_row if include_methods_and_attributes else ''}
            {attributes_rows if include_methods_and_attributes else ''}
            {methods_title_row if include_methods_and_attributes else ''}
            {methods_rows if include_methods_and_attributes else ''}
            {reduced_view_row if not include_methods_and_attributes else ''}
        </TABLE>>"""
        graph.node(class_name, label=label)

    for class_name, info in class_info.items():
        for base in info["bases"]:
            if base in class_info:
                graph.edge(base, class_name, arrowhead="onormal")

    return graph


def get_class_info_from_branch(repo_path, branch_name, filename):
    repo = Repo(repo_path)
    git = repo.git
    git.checkout(branch_name)
    file_path = os.path.join(repo_path, filename)
    return parse_class(file_path)


def convert_to_streams_path(base_name):
    base_name_lower = base_name.lower().replace("-", "_")
    return f"{base_name}/{base_name_lower}/streams.py"


AIRBYTE_REPO = "~/dev/airbyte"
AIRBYTE_SOURCES = "airbyte-integrations/connectors/"


def main(control_branch, target_branch, connector_name, show_only_differences):
    repo_path = os.path.expanduser(AIRBYTE_REPO)
    streams_path = os.path.join(repo_path, AIRBYTE_SOURCES, convert_to_streams_path(connector_name))
    class_info_control = get_class_info_from_branch(repo_path, control_branch, streams_path)
    class_info_target = get_class_info_from_branch(repo_path, target_branch, streams_path)

    differences = compare_classes(class_info_control, class_info_target)
    combined_class_info = combine_class_info(class_info_control, class_info_target)

    graph = class_info_to_uml(combined_class_info, differences, show_only_differences=show_only_differences)
    generated_uml = f"{connector_name}-streams-uml"
    graph.render(f'umls/{generated_uml}')

    print(f"UML diagram generated as '{generated_uml}'")


def run():
    parser = argparse.ArgumentParser(description="Generate UML diagrams from two git branches")
    parser.add_argument("--control-branch", type=str, required=True, help="Control branch to compare")
    parser.add_argument("--target-branch", type=str, required=True, help="Target branch to compare")
    parser.add_argument("--connector-name", type=str, required=True, help="File name to parse classes from")
    parser.add_argument("--show-only-differences", action="store_true",
                        help="Show only the differences in the UML diagram")

    args = parser.parse_args()

    main(args.control_branch, args.target_branch, args.connector_name, args.show_only_differences)