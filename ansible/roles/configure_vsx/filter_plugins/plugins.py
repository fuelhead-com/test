from ansible.template import Templar

class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_vsx_config": aoscx_generate_vsx_config
        }

def aoscx_generate_vsx_config(all_vars):
    templar = Templar(loader=None, variables=all_vars)
    result = {
        "config_attributes": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    vsx = all_vars.get("vsx", {}) or {}
    vsx_schema = all_vars.get("vsx_schema", {})
    post_attributes = all_vars.get("vsx_post_attributes")
    put_attributes = all_vars.get("vsx_put_attributes")
    get_vsx = all_vars.get("get_vsx")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in vsx_schema.items()
    }

    result["defaults"] = defaults

    device_role = vsx.get("device_role", defaults.get("device_role", None))

    isl_port = None
    inter_switch_link = vsx.get("inter_switch_link", defaults.get("inter_switch_link", None))

    if inter_switch_link is not None:
        isl_port = {
            inter_switch_link: f"/rest/{restversion}/system/interfaces/{inter_switch_link}"
        }

    keepalive_peer_ip = vsx.get("keepalive_peer_ip", defaults.get("keepalive_peer_ip", None))

    keepalive_src_ip = vsx.get("keepalive_src_ip", defaults.get("keepalive_src_ip", None))

    keepalive_vrf = None
    vrf = vsx.get("vrf", defaults.get("vrf", None))

    if vrf is not None:
        keepalive_vrf = {
            vrf: f"/rest/{restversion}/system/vrfs/{vrf}"
        }

    linkup_delay_timer = vsx.get("linkup_delay_timer", defaults.get("linkup_delay_timer", 180))

    split_recovery_disable = vsx.get("split_recovery_disable", defaults.get("split_recovery_disable", False))

    system_mac = templar.template(vsx.get("system_mac", defaults.get("system_mac", None)))

    config_attributes = {
        "device_role": device_role,
        "isl_port": isl_port,
        "keepalive_peer_ip": keepalive_peer_ip,
        "keepalive_src_ip": keepalive_src_ip,
        "keepalive_vrf": keepalive_vrf,
        "linkup_delay_timer": linkup_delay_timer,
        "split_recovery_disable": split_recovery_disable,
        "system_mac": system_mac
    }


    result["config_attributes"] = config_attributes

    vsx_configured = bool(get_vsx)
    vsx_required = bool(vsx)

    if vsx_configured and vsx_required:
        vsx_config = get_vsx

        compare = {
            key: vsx_config[key]
            for key in put_attributes
            if key in vsx_config
        }

        put_body = {
            key: config_attributes[key]
            for key in put_attributes
            if key in config_attributes
        }

        url = f"https://{ansible_host}/rest/{restversion}/system/vsx"

        if compare != put_body:
            put = {
                "body": put_body,
                "url": url
            }

            result["put"] = put

    if not vsx_configured and vsx_required:
        post_body = {
            key: config_attributes[key]
            for key in post_attributes
            if key in config_attributes
        }

        url = f"https://{ansible_host}/rest/{restversion}/system/vsx"

        post = {
            "body": post_body,
            "url": url
        }

        result["post"] = post

    if vsx_configured and not vsx_required:
        result["delete"] = {
            "url": f"https://{ansible_host}/rest/{restversion}/system/vsx"
        }

    return result