from ansible.template import Templar

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_snmp_vrf_config": aoscx_generate_snmp_vrf_config
        }

def aoscx_generate_snmp_vrf_config(all_vars):
    templar = Templar(loader=None, variables=all_vars)
    result = {
        "patch": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    snmp = all_vars.get("snmp", {}) or {}
    get_vrfs = all_vars.get("get_vrfs") or {}


    for vrf, value in get_vrfs.items():
        vrfs = snmp.get("vrfs", []) or []

        if value.get("snmp_enable"):
            if vrf not in vrfs:

                patch_body = {
                    "snmp_enable": False
                }

                url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}"

                patch = {
                    "body": patch_body,
                    "url": url
                }

                result["patch"][vrf] = patch

        elif not value.get("snmp_enable"):
            if vrf in vrfs:
                
                patch_body = {
                    "snmp_enable": True
                }

                url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}"

                patch = {
                    "body": patch_body,
                    "url": url
                }

                result["patch"][vrf] = patch

    return result