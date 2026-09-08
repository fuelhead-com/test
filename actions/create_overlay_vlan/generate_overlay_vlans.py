from pathlib import Path
from jinja2 import Environment, FileSystemLoader



# Jinja environment
env = Environment(
    loader=FileSystemLoader("templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)

# Template
template = env.get_template("vlan.yml.j2")

# Data
# data = {
#     "id": 250,
#     "name": "VLAN250",
#     "description": "Test Overlay Vlan 250",
#     "enabled": True,
#     "type": "overlay",
#     "scope": {
#         "type": "group",
#         "targets": [
#             "all_leafs",
#         ],
#     },
#     "tags": [
#         "devops"
#     ]
# }

data = [
    {
        "id": vlan_id,
        "name": f"VLAN{vlan_id}",
        "description": f"Test Overlay Vlan {vlan_id}",
        "enabled": True,
        "type": "overlay",
        "scope": {
            "type": "group",
            "targets": ["all_leafs"],
        },
        "tags": (
            ["devops"] if i % 3 == 0
            else ["standard"] if i % 3 == 1
            else ["devops", "standard"]
        ),
    }
    for i, vlan_id in enumerate(range(200, 400, 10))
]

for vlan in data:
# Render template
    output = template.render(**vlan)

# Filename based on VLAN ID
    filename = f"{vlan['id']}.yml"

    output_dir = Path(f"../ansible/network_data/vlans/{vlan['type']}")

    output_file = output_dir / filename

    # Write file
    output_file.write_text(output, encoding="utf-8")
