import yaml

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_evpn_vlan_config": aoscx_generate_evpn_vlan_config
        }

def aoscx_generate_evpn_vlan_config(all_vars):
    result = {
        "config_attributes": {},
        "compare": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    inventory_hostname = all_vars.get("inventory_hostname")
    group_names = all_vars.get("group_names")
    group_names.append("all")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    post_attributes = all_vars.get("evpn_vlan_post_attributes")
    put_attributes = all_vars.get("evpn_vlan_put_attributes")
    get_evpn_vlans = all_vars.get("get_evpn_vlans")
    overlay_vlan_files = all_vars.get("overlay_vlan_files")
    evpn_asn = all_vars.get("evpn_asn")

    all_overlay_vlans = {}

    for file in overlay_vlan_files:
        with open(file, "r", encoding="utf-8") as f:
            vlan = yaml.safe_load(f)

        all_overlay_vlans[vlan["id"]] = vlan

    switch_overlay_vlans = {}

    for vlan, value in all_overlay_vlans.items():
        if value.get("scope", {}).get("type") == "explicit":
            if inventory_hostname in value.get("scope", {}).get("targets"):
                switch_overlay_vlans[vlan] = value

        elif value.get("scope", {}).get("type") == "group":
            targets = value.get("scope", {}).get("targets", [])

            if any(x in group_names for x in targets):
                switch_overlay_vlans[vlan] = value

    result["switch_overlay_vlans"] = switch_overlay_vlans

    for vlan, value in switch_overlay_vlans.items():
        config_attributes = {
            "export_route_targets": [
                f"{evpn_asn}:{vlan}"
            ],
            "import_route_targets": [
                f"{evpn_asn}:{vlan}"
            ],
            "rd": "auto",
            "redistribute": {
                "host-route": False
            },
            "route_target_auto_mode": "default",
            "vlan": f"/rest/{restversion}/system/vlans/{vlan}"
        }

        result["config_attributes"][vlan] = config_attributes

        evpn_vlan_configured = str(vlan) in get_evpn_vlans.keys()

        if evpn_vlan_configured:
            evpn_vlan_config = get_evpn_vlans[str(vlan)]

            compare = {
                key: evpn_vlan_config[key]
                for key in put_attributes
                if key in evpn_vlan_config
            }

            result["compare"][vlan] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/evpn/evpn_vlans/{vlan}"

            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][vlan] = put

        else:
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/evpn/evpn_vlans"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][vlan] = post

    for vlan in get_evpn_vlans.keys():
        if int(vlan) not in switch_overlay_vlans.keys():

            result["delete"][vlan] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/evpn/evpn_vlans/{vlan}"
            }

    return result