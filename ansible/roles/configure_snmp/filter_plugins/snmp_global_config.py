from ansible.template import Templar

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_snmp_config": aoscx_generate_snmp_config
        }

def aoscx_generate_snmp_config(all_vars):
    templar = Templar(loader=None, variables=all_vars)
    result = {
        "config_attributes": {},
        "post": {},
        "patch": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    snmp = all_vars.get("snmp", {}) or {}
    snmp_schema = all_vars.get("snmp_schema", {})
    snmp_system_patch_attributes = all_vars.get("snmp_system_patch_attributes")
    snmp_system_other_config_patch_attributes = all_vars.get("snmp_system_other_config_patch_attributes")
    get_snmp_config = all_vars.get("get_snmp_config")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in snmp_schema.items()
    }

    result["defaults"] = defaults

    snmp_communities = templar.template(
        snmp.get(
            "snmp_communities",
            defaults.get("snmp_communities")
        )
    ) or []

    snmp_communities.sort()

    system_contact = templar.template(
        snmp.get(
            "system_contact",
            defaults.get("system_contact")
        )
    ) or None

    system_description = templar.template(
        snmp.get(
            "system_description",
            defaults.get("system_description")
        )
    ) or None

    system_location = templar.template(
        snmp.get(
            "system_location",
            defaults.get("system_location")
        ) or None
    )

    other_config = {
        **(
            {"system_contact": system_contact}
            if system_contact is not None
            else {}
        ),
        **(
            {"system_description": system_description}
            if system_description is not None
            else {}
        ),
        **(
            {"system_location": system_location}
            if system_location is not None
            else {}
        )
    }

    config_attributes = {
        "snmp_communities": snmp_communities,
        **(
            {"other_config": other_config}
            if other_config is not []
            else {}
        )
    }

    result["config_attributes"] = config_attributes

    other_config_compare = {
        key: get_snmp_config["other_config"][key]
        for key in snmp_system_other_config_patch_attributes
        if key in get_snmp_config["other_config"]
    }

    snmp_communities = get_snmp_config["snmp_communities"]

    compare = {
        "other_config": other_config_compare,
        "snmp_communities": snmp_communities,
    }

    result["compare"] = compare

    patch_body = {
        key: config_attributes[key]
        for key in snmp_system_patch_attributes
        if key in config_attributes
    }

    url = f"https://{ansible_host}/rest/{restversion}/system"

    if compare != patch_body:
        patch = {
            "body": patch_body,
            "url": url
        }

        result["patch"] = patch

    return result