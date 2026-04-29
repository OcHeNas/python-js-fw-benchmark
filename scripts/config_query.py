#!/usr/bin/env python3
import argparse
import copy
import json
import shlex
import sys
from pathlib import Path


def deep_merge(base, override):
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load_config(path, profile):
    with Path(path).open("r", encoding="utf-8") as handle:
        config = json.load(handle)

    profiles = config.get("profiles", {})
    if profile not in profiles:
        raise SystemExit(f"Unknown benchmark profile: {profile}")

    return deep_merge(config, profiles[profile])


def emit_shell(config, profile):
    tests = config["tests"]
    variables = {
        "BENCH_CONFIG_PROFILE": profile,
        "SERVICE_PORT": config["service"]["internal_port"],
        "STARTUP_TIMEOUT_SECONDS": config["service"].get("startup_timeout_seconds", 60),
        "MONITOR_INTERVAL_SECONDS": config.get("monitor", {}).get("interval_seconds", 2),
        "FRAMEWORKS": " ".join(config["frameworks"]),
        "TESTS": " ".join(tests.keys()),
    }

    for test_name, test_config in tests.items():
        prefix = f"TEST_{test_name.upper()}"
        variables[f"{prefix}_SCRIPT"] = test_config["script"]
        variables[f"{prefix}_VUS"] = test_config["vus"]
        variables[f"{prefix}_DURATION"] = test_config["duration"]

    for name, value in variables.items():
        print(f"{name}={shlex.quote(str(value))}")


def main():
    parser = argparse.ArgumentParser(description="Read benchmark config values.")
    parser.add_argument("command", choices=["shell"])
    parser.add_argument("--config", default="config/test_config.yaml")
    parser.add_argument("--profile", default="default")
    args = parser.parse_args()

    try:
        config = load_config(args.config, args.profile)
    except json.JSONDecodeError as exc:
        print(
            f"{args.config} must be JSON-compatible YAML so it can be parsed without extra dependencies: {exc}",
            file=sys.stderr,
        )
        return 2

    if args.command == "shell":
        emit_shell(config, args.profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
