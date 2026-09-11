class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_physical_ospf_interface_config": aoscx_generate_physical_ospf_interface_config,
            "aoscx_generate_physical_ospf_active_interface_config": aoscx_generate_physical_ospf_active_interface_config
        }

def aoscx_generate_physical_ospf_interface_config(all_vars):

    result = {
        "enable_ospf_interfaces": {},
        "disable_ospf_interfaces": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    physical_interfaces = all_vars.get("physical_interfaces", {}) or {}
    get_ospf_interfaces = all_vars.get("get_ospf_interfaces", {})
    get_physical_interfaces = all_vars.get("get_physical_interfaces", {})

    ospf_interfaces = {
        interface: value
        for interface, value in physical_interfaces.items()
        if value.get("ip_ospf_process") != None 
        and value.get("ip_ospf_area") != None
        and value.get("routing")
    }

    result["ospf_interfaces"] = ospf_interfaces

    enable_routing = {
        interface: {
            "body": {
                "routing": True
            },
            "url": f"https://{ansible_host}/rest/{restversion}/system/interfaces/{interface.replace('/', '%2F')}"
        }
        for interface, value in ospf_interfaces.items()
        if not get_physical_interfaces.get(interface, {}).get("routing", True)
    }

    result["enable_routing"] = enable_routing

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
                    if value["port"][interface]["type"] == "system":
                        if interface not in ospf_interfaces.keys() or int(process) != ospf_interfaces[interface]["ip_ospf_process"]:

                            result["disable_ospf_interfaces"][interface] = {
                                "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers/{process}/areas/{area}/ospf_interfaces/{interface.replace('/', '%2F')}"
                            }
                        
    return result

def aoscx_generate_physical_ospf_active_interface_config(all_vars):

    result = {
        "patch": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    physical_interfaces = all_vars.get("physical_interfaces", {}) or {}
    get_ospf_active_interfaces = all_vars.get("get_ospf_active_interfaces", {})

    ospf_interfaces = {
        interface: value
        for interface, value in physical_interfaces.items()
        if value.get("ip_ospf_process") != None 
        and value.get("ip_ospf_area") != None
        and value.get("routing")
    }

    result["ospf_interfaces"] = ospf_interfaces

    for interface, value in ospf_interfaces.items():
        vrf = value.get("vrf") or "default"
        process = str(value.get("ip_ospf_process"))

        configured_active_interfaces = get_ospf_active_interfaces.get(vrf, {}).get(process, {}).get("active_interfaces")

        if interface not in configured_active_interfaces.keys():
            result["patch"][interface] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers/{process}",
                "body": {
                    "active_interfaces": {
                        interface: f"/rest/{restversion}/system/interfaces/{interface.replace('/', '%2F')}"
                    }
                }
            }


    return result