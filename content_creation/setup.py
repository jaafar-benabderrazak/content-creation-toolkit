#!/usr/bin/env python
"""
First-run setup: scans environment variables and writes a starter pipeline profile.

Usage:
    python setup.py [--output config/profiles/starter.yaml] [--force]

Options:
    --output PATH   Output YAML path (default: config/profiles/starter.yaml)
    --force         Overwrite existing file without prompting
"""

import argparse
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Known environment variables — ordered by priority
# Fields with field=None are noted but not injected into PipelineConfig
# ---------------------------------------------------------------------------
KNOWN_ENV_VARS = [
    {
        "env": "NOTF_DISCORD_WEBHOOK_URL",
        "field": "notify.discord_webhook_url",
        "description": "Discord webhook for pipeline notifications",
    },
    {
        "env": "NOTF_SLACK_WEBHOOK_URL",
        "field": "notify.slack_webhook_url",
        "description": "Slack webhook for pipeline notifications",
    },
    {
        "env": "SUNO_API_KEY",
        "field": "suno.api_key",
        "description": "Suno music generation API key (kie.ai)",
    },
    {
        "env": "OPENAI_API_KEY",
        "field": None,
        "description": "OpenAI API key (used in Phase 18 prompt generation)",
    },
    {
        "env": "REPLICATE_API_TOKEN",
        "field": None,
        "description": "Replicate API token for SDXL fallback",
    },
    {
        "env": "YOUTUBE_QUOTA_USED",
        "field": None,
        "description": "YouTube daily quota tracker (set by publisher after upload)",
    },
]


def _inject_field(config, dotted_field: str, value: str):
    """
    Inject a value into a nested PipelineConfig using a dotted path.
    e.g. "notify.discord_webhook_url" -> config.notify.discord_webhook_url = value

    Supports Pydantic v2 (model_copy) and v1 (copy) via fallback.
    """
    parts = dotted_field.split(".", 1)
    if len(parts) != 2:
        return config
    section_name, key = parts

    section_obj = getattr(config, section_name, None)
    if section_obj is None:
        # Section is None (e.g. suno not initialised); skip injection
        return config

    try:
        updated_section = section_obj.model_copy(update={key: value})
    except AttributeError:
        updated_section = section_obj.copy(update={key: value})  # Pydantic v1

    try:
        config = config.model_copy(update={section_name: updated_section})
    except AttributeError:
        config = config.copy(update={section_name: updated_section})  # Pydantic v1

    return config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan environment variables and write a starter pipeline profile.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        default="config/profiles/starter.yaml",
        metavar="PATH",
        help="Output YAML path (default: config/profiles/starter.yaml)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing file without prompting",
    )
    args = parser.parse_args()

    # -----------------------------------------------------------------------
    # Scan env vars
    # -----------------------------------------------------------------------
    found: dict[str, str] = {}
    missing: list[dict] = []

    for entry in KNOWN_ENV_VARS:
        val = os.environ.get(entry["env"])
        if val:
            found[entry["env"]] = val
        else:
            missing.append(entry)

    # -----------------------------------------------------------------------
    # Build PipelineConfig with defaults
    # -----------------------------------------------------------------------
    # Add project root to sys.path so the import works regardless of cwd
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from config.pipeline_config import PipelineConfig  # noqa: E402

    config = PipelineConfig()

    # Inject found values for entries that have a mapped field
    for entry in KNOWN_ENV_VARS:
        if entry["field"] is not None and entry["env"] in found:
            config = _inject_field(config, entry["field"], found[entry["env"]])

    # -----------------------------------------------------------------------
    # Guard: existing file without --force
    # -----------------------------------------------------------------------
    output_path = Path(args.output)
    if output_path.exists() and not args.force:
        print(
            f"[setup.py] File already exists: {output_path}\n"
            "Use --force to overwrite.",
            file=sys.stderr,
        )
        sys.exit(0)

    # -----------------------------------------------------------------------
    # Write profile
    # -----------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    config.to_yaml(output_path)

    # -----------------------------------------------------------------------
    # Print summary
    # -----------------------------------------------------------------------
    print(f"\nStarter profile written to: {output_path}\n")

    if found:
        mapped = [e for e in KNOWN_ENV_VARS if e["env"] in found and e["field"] is not None]
        noted = [e for e in KNOWN_ENV_VARS if e["env"] in found and e["field"] is None]
        if mapped:
            print("Found (pre-filled):")
            max_env_len = max(len(e["env"]) for e in mapped)
            for entry in mapped:
                print(f"  {entry['env']:<{max_env_len}}  -> {entry['field']}")
            print()
        if noted:
            print("Found (noted, no config field yet):")
            for entry in noted:
                print(f"  {entry['env']}")
            print()
    else:
        print("Found (pre-filled): (none)\n")

    if missing:
        print("Missing (set these in .env or export before running pipelines):")
        max_env_len = max(len(e["env"]) for e in missing)
        for entry in missing:
            print(f"  {entry['env']:<{max_env_len}}  — {entry['description']}")
        print()
    else:
        print("Missing: (none — all known env vars are set)\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
