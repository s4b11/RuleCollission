from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..engine.loader import RulePackError, validate
from ..engine.models import RulePack
from ..models import RulePackVersion


def active_row(db: Session, org_id: str, pack_id: str) -> RulePackVersion | None:
    query = select(RulePackVersion).where(
        RulePackVersion.org_id == org_id, RulePackVersion.pack_id == pack_id, RulePackVersion.active
    )
    return db.scalars(query).first()


def active_pack(db: Session, org_id: str, pack_id: str) -> RulePack:
    row = active_row(db, org_id, pack_id)
    if not row:
        raise LookupError(f"No active rule pack '{pack_id}'")
    return RulePack.model_validate(row.data)


def check(data: dict) -> RulePack:
    try:
        return validate(RulePack.model_validate(data))
    except ValidationError as error:
        raise RulePackError(str(error))


def save_version(db: Session, org_id: str, data: dict, created_by: str) -> RulePackVersion:
    pack = check(data)
    previous = active_row(db, org_id, pack.pack_id)
    version = 1
    if previous:
        previous.active = False
        version = previous.version + 1
    row = RulePackVersion(
        org_id=org_id, pack_id=pack.pack_id, version=version,
        data=pack.model_dump(mode="json", exclude_none=True), created_by=created_by,
    )
    db.add(row)
    db.flush()
    return row
