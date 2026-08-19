"""Strands-agent provider for promptfoo (AWSMCPSkillsEval).

This wraps a Strands agent as a promptfoo Python provider so the same test
suite can run the agent twice: once with the PCI skill loaded and once without
(baseline). The agent is given ONLY read-only tools — kubectl get/describe,
AWS CLI describe/list/get, CloudWatch reads, and read-only filesystem access to
the skill's own reference files. There is no mutating tool, which mirrors the
skill's "strictly read-only" contract and guarantees that even a live run
against a real AWS account cannot change cluster or account state.

promptfoo calls `call_api(prompt, options, context)` and expects a dict with an
`output` key (and optionally `tokenUsage`, `cost`, `metadata`).

Config (from promptfooconfig.yaml `providers[].config`):
    model:     Bedrock model id for the Strands agent.
    skill:     "none" for baseline, or the skill name to load SKILL.md +
               references into the agent's system context.
    skill_dir: path (relative to this file) to the skill repo root.
    tools:     list of read-only tool groups to enable.

This module is intentionally dependency-light at import time; the Strands SDK
and boto3 are imported lazily inside call_api so that offline (live:false)
routing tests can run in CI without cloud credentials if the harness stubs the
agent. See README.md for the full setup.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

# --- Read-only tool registry -------------------------------------------------
# Every tool here is allow-listed to non-mutating verbs. The agent physically
# cannot call apply/delete/patch/exec or any AWS write API.

KUBECTL_RO_VERBS = {"get", "describe", "version", "auth", "api-resources"}
AWS_RO_PREFIXES = ("describe", "list", "get")


def _load_skill_context(skill_dir: Path, skill_name: str) -> str:
    """Return the SKILL.md + reference tree as a single system-context string.

    Mirrors how AWSMCPSkillsEval surfaces a skill to the Strands agent: the
    SKILL.md front-matter/body is injected, and reference files are made
    readable on demand via the fs_ro tool. We inline SKILL.md here and let the
    agent pull reference files itself so we can measure whether it reads the
    right pillar file (matches the skill's "read one pillar at a time" rule).
    """
    skill_md = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    return (
        f"You have access to the '{skill_name}' skill. Its instructions "
        f"follow. Reference files under references/ are readable with the "
        f"fs_ro tool.\n\n<SKILL>\n{skill_md}\n</SKILL>\n"
    )


def _build_agent(config: Dict[str, Any]):
    """Construct the Strands agent with read-only tools and (optional) skill."""
    from strands import Agent  # lazy import
    from strands.models import BedrockModel

    skill_dir = (Path(__file__).parent / config.get("skill_dir", "../")).resolve()
    skill_name = config.get("skill", "none")

    system_parts: List[str] = [
        "You are an AWS/EKS engineering agent operating in a customer account. "
        "You may only use read-only tools. Never run mutating commands."
    ]
    if skill_name and skill_name != "none":
        system_parts.append(_load_skill_context(skill_dir, skill_name))

    model = BedrockModel(model_id=config["model"])
    tools = _resolve_tools(config.get("tools", []), skill_dir)
    return Agent(model=model, system_prompt="\n\n".join(system_parts), tools=tools)


def _resolve_tools(tool_groups: List[str], skill_dir: Path) -> list:
    """Return read-only Strands tools for the requested groups."""
    from strands import tool

    tools: list = []

    if "kubectl_ro" in tool_groups:

        @tool
        def kubectl(args: str) -> str:
            """Run a READ-ONLY kubectl command (get/describe/version/auth only)."""
            verb = args.strip().split()[0] if args.strip() else ""
            if verb not in KUBECTL_RO_VERBS:
                return f"REFUSED: '{verb}' is not a read-only kubectl verb."
            return _run(["kubectl", *args.split()])

        tools.append(kubectl)

    if "aws_ro" in tool_groups or "cloudwatch_ro" in tool_groups:

        @tool
        def aws(args: str) -> str:
            """Run a READ-ONLY AWS CLI command (describe/list/get operations)."""
            parts = args.split()
            # parts[0]=service, parts[1]=operation
            op = parts[1] if len(parts) > 1 else ""
            if not op.startswith(AWS_RO_PREFIXES):
                return f"REFUSED: '{op}' is not a read-only AWS operation."
            return _run(["aws", *parts])

        tools.append(aws)

    if "fs_ro" in tool_groups:

        @tool
        def read_reference(rel_path: str) -> str:
            """Read a file under the skill's references/ directory (read-only)."""
            target = (skill_dir / rel_path).resolve()
            if not str(target).startswith(str(skill_dir)):
                return "REFUSED: path escapes skill directory."
            if not target.exists():
                return f"NOT FOUND: {rel_path}"
            return target.read_text(encoding="utf-8")

        tools.append(read_reference)

    return tools


def _run(cmd: List[str]) -> str:
    import subprocess

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return proc.stdout if proc.returncode == 0 else f"ERROR: {proc.stderr}"
    except Exception as exc:  # noqa: BLE001
        return f"ERROR: {exc}"


def call_api(prompt: str, options: Dict[str, Any], context: Dict[str, Any]):
    """promptfoo entry point."""
    config = options.get("config", {}) or {}

    # Offline routing tests can short-circuit the real agent when the harness
    # sets PROMPTFOO_STUB_AGENT=1, returning a deterministic transcript so
    # selection assertions can run without cloud credentials.
    if os.environ.get("PROMPTFOO_STUB_AGENT") == "1":
        # Return cost/tokenUsage so cost/latency assertions have data to grade
        # against; toolCalls is empty because no real agent ran.
        return {
            "output": _stubbed_output(prompt, config),
            "cost": 0.0,
            "tokenUsage": {"total": 0, "prompt": 0, "completion": 0},
            "metadata": {"stubbed": True, "toolCalls": []},
        }

    agent = _build_agent(config)
    result = agent(prompt)

    # Strands returns a result object; normalize to text + tool trace.
    text = getattr(result, "message", None) or str(result)
    tool_calls = [
        {"name": m.get("name"), "input": m.get("input")}
        for m in getattr(result, "tool_calls", []) or []
    ]
    usage = getattr(result, "usage", {}) or {}
    return {
        "output": text,
        "cost": float(getattr(result, "cost", 0.0) or 0.0),
        "tokenUsage": {
            "total": usage.get("total_tokens", 0),
            "prompt": usage.get("input_tokens", 0),
            "completion": usage.get("output_tokens", 0),
        },
        "metadata": {
            "toolCalls": tool_calls,
            "skillLoaded": config.get("skill", "none") != "none",
        },
    }


def _stubbed_output(prompt: str, config: Dict[str, Any]) -> str:
    """Deterministic placeholder for offline runs (documented in README)."""
    loaded = config.get("skill", "none") != "none"
    return (
        f"[STUB agent skill_loaded={loaded}] Received prompt: {prompt[:200]}"
    )
