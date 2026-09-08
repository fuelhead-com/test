import argparse
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

def vlan_id(value):
    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("VLAN ID must be an integer")

    if not 10 <= value <= 3999:
        raise argparse.ArgumentTypeError(
            "VLAN ID must be between 10 and 3999"
        )

    return value

def vlan_name(value):
    value = value.strip()

    if not value:
        raise argparse.ArgumentTypeError(
            "VLAN name cannot be empty"
        )

    if "\n" in value or "\r" in value:
        raise argparse.ArgumentTypeError(
            "VLAN name cannot contain newlines"
        )

    return value

def vlan_description(value):
    value = value.strip()

    if "\n" in value or "\r" in value:
        raise argparse.ArgumentTypeError(
            "VLAN description cannot contain newlines"
        )

    return value

def boolean(value):
    value = value.lower()

    if value == "true":
        return True

    if value == "false":
        return False

    raise argparse.ArgumentTypeError(
        "Boolean value must be true or false"
    )

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", required=True, type=vlan_id)
    parser.add_argument(
        "--name",
        required=True,
        type=vlan_name,
    )

    parser.add_argument(
        "--description",
        type=vlan_description,
    )

    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
    )

    parser.add_argument(
        "--vlan-tag-standard",
        type=boolean,
        default=True,
    )

    parser.add_argument(
        "--vlan-tag-devops",
        type=boolean,
        default=False,
    )

    parser.add_argument(
        "--igmp-snooping",
        type=boolean,
        default=False,
    )

    args = parser.parse_args()

    description = args.description or f"Overlay VLAN {args.id} - {args.name}"

    vlan_tagging = []

    if args.vlan_tag_standard:
        vlan_tagging.append("standard")

    if args.vlan_tag_devops:
        vlan_tagging.append("devops")

    # Paths
    action_dir = Path(__file__).resolve().parent
    base_dir = action_dir.parent.parent

    template_dir = action_dir / "templates"

    output_dir = (
        base_dir
        / "ansible"
        / "network_data"
        / "vlans"
        / "overlay"
    )

    # Jinja environment
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template("vlan.yml.j2")

    # Data to Jinja
    data = {
        "id": args.id,
        "name": args.name,
        "description": description,
        "enabled": True,
        "igmp_snooping": args.igmp_snooping,
        "type": "overlay",
        "scope": {
            "type": "group",
            "targets": args.targets,
        },
        "vlan_tagging": vlan_tagging,
    }

    # Render template
    output = template.render(**data)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Output filename
    output_file = output_dir / f"{args.id}.yml"

    # Don't overwrite existing VLAN
    try:
        with open(output_file, "x", encoding="utf-8") as f:
            f.write(output)
    except FileExistsError:
        parser.error(
            f"VLAN file already exists and will not be overwritten: "
            f"{output_file}"
        )

    print(f"Created: {output_file}")


if __name__ == "__main__":
    main()