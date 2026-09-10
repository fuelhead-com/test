class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_ospf_area_config": aoscx_generate_ospf_area_config
        }

def aoscx_generate_ospf_area_config(all_vars):
    result = {
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    router_ospf = all_vars.get("router_ospf", {})
    router_ospf_schema = all_vars.get("router_ospf_schema")
    ospf_area_schema = router_ospf_schema.get("instance", {}).get("areas", {}).get("area")
    post_attributes = all_vars.get("ospf_area_post_attributes")
    put_attributes = all_vars.get("ospf_area_put_attributes")
    get_ospf_areas = all_vars.get("get_ospf_areas")

    defaults = {
        key: value.get("default",) if value else None
        for key, value in ospf_area_schema.items()
    }
    defaults["vrf"] = router_ospf_schema.get("instance", {}).get("vrf", {}).get("default") or "default"

    for router, value in router_ospf.items():
        value = value or {}

        areas = value.get("areas") or {}
        vrf = value.get("vrf") or defaults.get("vrf")

        for area, value in areas.items():
            value = value or {}
            area_configured = area in get_ospf_areas.get(vrf, {}).get(str(router), {}).keys()

            config_attributes = {
                "area_id": area,
                "area_type": value.get("area_type") or defaults.get("area_type") or "default",
                "other_config": {
                    "stub_default_cost": value.get("default_metric") or defaults.get("default_metric"),
                    "stub_metric_type": "metric_non_comparable"
                }
            }

            if area_configured:
                area_config = get_ospf_areas[vrf][str(router)][area]

                compare = {
                    key: area_config[key]
                    for key in put_attributes
                    if key in area_config
                }

            else:
                compare = None

            if not compare:
                post_body = {
                    key: config_attributes[key]
                    for key in post_attributes
                    if key in config_attributes
                }

                url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers/{router}/areas"

                post = {
                    "body": post_body,
                    "url": url
                }

                result["post"][f"ospf_router_{router}_area_{area}"] = post

            elif compare:
                put_body = {
                    key: config_attributes[key]
                    for key in put_attributes
                    if key in config_attributes
                }

                url = f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers/{router}/areas/{area}"

                if compare != put_body:
                    put = {
                        "body": put_body,
                        "url": url
                    }

                    result["put"][f"ospf_router_{router}_area_{area}"] = put


    for vrf, routers in get_ospf_areas.items():
        routers = routers or {}

        for router, areas in routers.items():
            areas = areas or {}

            for area, value in areas.items():
                value = value or {}

            if area not in router_ospf.get(int(router), {}).get("areas", {}).keys():
                result["delete"][f"ospf_router_{router}_area_{area}"] = {
                    "url": f"https://{ansible_host}/rest/{restversion}/system/vrfs/{vrf}/ospf_routers/{router}/areas/{area}"
                }

    return result