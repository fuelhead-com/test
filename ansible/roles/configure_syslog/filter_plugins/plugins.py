class FilterModule(object):
    def filters(self):
        return {
            "aoscx_generate_syslog_remotes_config": aoscx_generate_syslog_remotes_config
        }


def aoscx_generate_syslog_remotes_config(all_vars):

    # Build the result structure containing the normalized configuration
    # and the REST operations required to reach the desired state.
    result = {
        "config_attributes": {},
        "compare": {},
        "post": {},
        "put": {},
        "delete": {}
    }

    ansible_host = all_vars.get("ansible_host")
    aoscx_api_version = all_vars.get("aoscx_api_version")
    restversion = f"v{aoscx_api_version}"
    syslog_remotes = all_vars.get("syslog_remotes", {}) or {}
    syslog_remotes_schema = all_vars.get("syslog_remotes_schema", {}).get("remote", {})
    post_attributes = all_vars.get("syslog_remotes_post_attributes")
    put_attributes = all_vars.get("syslog_remotes_put_attributes")
    get_syslog_remotes = all_vars.get("get_syslog_remotes")

    # Extract default values from the schema so that user input and
    # schema defaults are handled consistently.
    defaults = {
        key: value.get("default",) if value else None
        for key, value in syslog_remotes_schema.items()
    }

    result["defaults"] = defaults

    for srv, value in syslog_remotes.items():
        value = value or {}

        disable = value.get("enabled", defaults.get("enabled", True)) is False

        port_number = value.get("port_number", defaults.get("port_number")) or None

        rate_limit_interval = value.get(
            "rate_limit_interval",
            defaults.get("rate_limit_interval")
        ) or 30

        rate_limit_burst = value.get(
            "rate_limit_burst",
            defaults.get("rate_limit_burst")
        ) or None

        rate_limit = {
            **({"burst": rate_limit_burst} if rate_limit_burst is not None else {}),
            "interval": rate_limit_interval,
        }

        severity = value.get("severity", defaults.get("severity")) or "info"

        transport = value.get("protocol", defaults.get("protocol")) or "udp"

        remote_host = srv

        vrf_name = value.get("vrf", defaults.get("vrf")) or "default"

        # ArubaOS-CX expects the VRF as a resource reference rather than
        # just the VRF name.
        vrf = {
            vrf_name: f"/rest/{restversion}/system/vrfs/{vrf_name}"
        }

        # Normalize the desired configuration into the format expected by
        # the ArubaOS-CX REST API. This representation is reused for both
        # POST and PUT requests.
        config_attributes = {
            "disable": disable,
            "port_number": port_number,
            "rate_limit": rate_limit,
            "remote_host": remote_host,
            "severity": severity,
            "transport": transport,
            "vrf": vrf,
        }

        result["config_attributes"][srv] = config_attributes

        # Check whether this syslog server already exists in the current
        # configuration retrieved from the switch.
        srv_configured = srv in get_syslog_remotes.keys()

        # If server is already configured, check if configuration needs update
        if srv_configured:
            srv_config = get_syslog_remotes[srv]

            # Compare only attributes that are valid for PUT operations.
            # This prevents unrelated or read-only attributes from affecting
            # the comparison.
            compare = {
                key: srv_config[key]
                for key in put_attributes
                if key in srv_config
            }

            result["compare"][srv] = compare

            put_body = {
                key: config_attributes[key]
                for key in put_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/syslog_remotes/{srv}"

            # Generate a PUT only when the current configuration differs from
            # the desired configuration. This keeps the operation idempotent
            # and avoids unnecessary API calls.
            if compare != put_body:
                put = {
                    "body": put_body,
                    "url": url
                }

                result["put"][srv] = put

        # The server does not exist in the current configuration, so
        # generate a POST request to create it.
        elif not srv_configured:
            # POST and PUT may support different sets of attributes, so build
            # the request body according to the attributes allowed for each operation.
            post_body = {
                key: config_attributes[key]
                for key in post_attributes
                if key in config_attributes
            }

            url = f"https://{ansible_host}/rest/{restversion}/system/syslog_remotes"

            post = {
                "body": post_body,
                "url": url
            }

            result["post"][srv] = post

    # Remove servers that exist in the current configuration but are
    # no longer present in the desired configuration.
    #
    # This makes the filter manage the complete lifecycle of a syslog
    # remote: create, update, and delete.
    for srv in get_syslog_remotes:

        if srv not in syslog_remotes.keys():
            result["delete"][srv] = {
                "url": f"https://{ansible_host}/rest/{restversion}/system/syslog_remotes/{srv}"
            }

    return result
