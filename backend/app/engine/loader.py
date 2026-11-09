from __future__ import annotations

from pathlib import Path

import yaml

from .analyzer import atoms
from .models import RulePack

RULEPACK_DIR = Path(__file__).resolve().parents[3] / "rulepacks"


class RulePackError(ValueError):
    pass


def validate(pack: RulePack) -> RulePack:
    offices = {o.id for o in pack.offices}
    docs = {d.id for d in pack.documents}
    aliases = {a for d in pack.documents for a in d.aliases}
    errors: list[str] = []

    clash = docs & aliases
    if clash:
        errors.append(f"aliases shadow document ids: {sorted(clash)}")
    for r in [*pack.requirements, *pack.alternatives]:
        if r.office not in offices:
            errors.append(f"{r.id}: unknown office '{r.office}'")
        if r.produces not in docs:
            errors.append(f"{r.id}: unknown produced document '{r.produces}'")
        for t in atoms(r.prerequisites):
            if t not in docs and t not in aliases:
                errors.append(f"{r.id}: unknown prerequisite '{t}'")
    for a in pack.alternatives:
        if a.approval_by not in offices:
            errors.append(f"{a.id}: unknown approval office '{a.approval_by}'")
        if a.substitutes not in docs:
            errors.append(f"{a.id}: unknown substituted document '{a.substitutes}'")
        for o in a.in_offices:
            if o not in offices:
                errors.append(f"{a.id}: unknown accepting office '{o}'")
    ids = [r.id for r in [*pack.requirements, *pack.alternatives]]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        errors.append(f"duplicate ids: {sorted(dupes)}")
    if errors:
        raise RulePackError(f"Rule pack '{pack.pack_id}' is invalid:\n- " + "\n- ".join(errors))
    return pack


def load_rulepack(name_or_path: str | Path) -> RulePack:
    path = Path(name_or_path)
    if not path.suffix:
        path = RULEPACK_DIR / f"{name_or_path}.yaml"
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return validate(RulePack.model_validate(data))


def available_rulepacks() -> list[str]:
    return sorted(p.stem for p in RULEPACK_DIR.glob("*.yaml"))
