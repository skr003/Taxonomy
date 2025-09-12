#!/usr/bin/env python3
import os
import json
import argparse
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree

WORKSPACE_DIR = os.path.join(os.getcwd(), "forensic_workspace")

CATEGORY_FILES = {
    "system_logs.json": "System Logs and Events",
    "user_activity.json": "User Activity and Commands",
    "network.json": "Network Connections and Configuration",
    "configuration.json": "System and User Configuration",
    "applications.json": "Application and Service Configurations",
    "processes.json": "Processes and Memory",
    "files.json": "Files and Directories Metadata",
    "packages.json": "Package Management and Installed Software",
    "other.json": "Other Potential Evidence Paths"
}

def create_mindmap(json_data, root_name):
    """Convert JSON logs into a FreeMind (.mm) XML mindmap."""
    root = Element("map", version="1.0.1")
    node = SubElement(root, "node", TEXT=f"Forensic Case: {json_data.get('case_id', 'N/A')}")

    meta_node = SubElement(node, "node", TEXT=f"Timestamp: {json_data.get('timestamp', '')}")
    category_node = SubElement(node, "node", TEXT=root_name)

    for item in json_data.get("items", []):
        item_text = item.get("name") or item.get("message") or str(item)
        child = SubElement(category_node, "node", TEXT=item_text)

        # Add raw/meta details if available
        if "meta" in item:
            raw = item["meta"].get("raw")
            if raw:
                SubElement(child, "node", TEXT=f"Raw: {raw}")

    return root


def export_mindmap(infile, outfile, category_name):
    with open(infile, "r") as f:
        data = json.load(f)

    root = create_mindmap(data, category_name)
    tree = ElementTree(root)
    tree.write(outfile, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    output_dir = os.path.join(WORKSPACE_DIR, "mindmaps")
    os.makedirs(output_dir, exist_ok=True)

    for filename, category in CATEGORY_FILES.items():
        infile = os.path.join(WORKSPACE_DIR, filename)
        outfile = os.path.join(output_dir, f"{filename}.mm")

        if os.path.exists(infile):
            export_mindmap(infile, outfile, category)
            print(f"[INFO] Exported {outfile}")
        else:
            print(f"[WARN] Missing file: {infile}")

    # Also handle combined logs
    combined_file = os.path.join(WORKSPACE_DIR, "formatted_logs.json")
    if os.path.exists(combined_file):
        export_mindmap(combined_file, os.path.join(output_dir, "formatted_logs.mm"), "All Categories")
        print("[INFO] Exported combined formatted_logs.mm")
