# Vendored copy of nas-stuff forgejo/wf_triggers.py (keep in sync); run via scripts/check-github-triggers.
"""Can a push mirror start this GitHub workflow?  Used by flip-mirror.sh --allow-actions-on.

    python3 wf_triggers.py < workflow.yml     # exit 0 + "ok, triggers: ..." or exit 1 + reason

Fail-closed: anything it can't read as a plain mapping with a single, well-formed `on:` is refused.
Run it with PyYAML pinned: `uv run --no-project --with pyyaml==6.0.3 python3 wf_triggers.py`.
"""

import sys

import yaml

# Events a mirror push (branches, tags, force-updates, deletions) can fire, directly or as a follow-on.
FORBIDDEN = frozenset(
    {"push", "pull_request", "pull_request_target", "create", "delete", "release", "workflow_run"}
)


class Refused(Exception):
    pass


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate keys in any mapping (incl. `on` vs `true`)."""

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)  # resolves `<<` merge keys first, like SafeLoader does
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)
            if key is True:  # YAML 1.1 reads a bare `on` as boolean true
                key = "on"
            try:
                dup = key in seen
            except TypeError:
                raise Refused(f"unhashable mapping key at line {key_node.start_mark.line + 1}")
            if dup:
                raise Refused(f"duplicate key {key!r} at line {key_node.start_mark.line + 1}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def triggers(text: str) -> list[str]:
    """Return the workflow's trigger names, or raise Refused."""
    try:
        doc = yaml.load(text, Loader=_StrictLoader)  # noqa: S506 (SafeLoader subclass)
    except Refused:
        raise
    except yaml.YAMLError as e:
        raise Refused(f"YAML parse error: {e}".splitlines()[0])
    if not isinstance(doc, dict):
        raise Refused(f"top level is {type(doc).__name__}, not a mapping")
    keys = [k for k in doc if k == "on" or k is True]
    if len(keys) != 1:
        raise Refused("no `on:` key" if not keys else "both `on` and `true` keys")
    on = doc[keys[0]]
    if isinstance(on, str):
        names = [on]
    elif isinstance(on, list):
        names = on
    elif isinstance(on, dict):
        names = list(on)
    else:
        raise Refused(f"`on:` is {type(on).__name__}, want str, list or mapping")
    if not names:
        raise Refused("`on:` is empty")
    for n in names:
        if not isinstance(n, str) or not n.replace("_", "").isalnum():
            raise Refused(f"trigger name {n!r} is not a plain event name")
    bad = sorted(FORBIDDEN & set(names))
    if bad:
        raise Refused("push-type triggers: " + ",".join(bad))
    return sorted(set(names))


def main() -> int:
    try:
        names = triggers(sys.stdin.read())
    except Refused as e:
        print(e)
        return 1
    print("ok, triggers:", " ".join(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
