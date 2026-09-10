class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_loopback_ospf_interface_config": aoscx_generate_loopback_ospf_interface_config
        }

def aoscx_generate_loopback_ospf_interface_config(all_vars):

    result = {
        "enable_ospf_interfaces": {},
        "disable_ospf_interfaces": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    loopback_interfaces = all_vars.get("loopback_interfaces", {}) or {}
    get_ospf_interfaces = all_vars.get("get_ospf_interfaces", {})

    ospf_interfaces = {
        interface: value
        for interface, value in loopback_interfaces.items()
        if value.get("ip_ospf_process") != None 
        and value.get("ip_ospf_area") != None
    }

    result["ospf_interfaces"] = ospf_interfaces


    for interface, value in ospf_interfaces.items():
        vrf = value.get("vrf", "default")
        process = value.get("ip_ospf_process")
        area = value.get("ip_ospf_area")

        ospf_interface_configured = get_ospf_interfaces.get(vrf, {}).get(str(process), {}).get(area, {}).get(interface)

        if not ospf_interface_configured:

            body = {
                "instance_id": process,
                "interface_name": interface,
                "port": {
                    interface: f"/rest/{restversion}/system/interfaces/{interface.replace('/', '%2F')}"
                }
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers/{process}/areas/{area}/ospf_interfaces"

            post = {
                "body": body,
                "url": url
            }

            result["enable_ospf_interfaces"][interface] = post

    for vrf, processes in get_ospf_interfaces.items():
        for process, areas in processes.items():
            for area, interfaces in areas.items():
                for interface, value in interfaces.items():
                    if interface not in ospf_interfaces.keys() and value["port"][interface]["type"] == "loopback":

                        result["disable_ospf_interfaces"][interface] = {
                            "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers/{process}/areas/{area}/ospf_interfaces/{interface.replace('/', '%2F')}"
                        }
                        
    return result