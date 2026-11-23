from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.lead import WorkflowRun
from app.schemas.internal import WorkflowRunCreate


def log_workflow_run(db: Session, data: WorkflowRunCreate) -> WorkflowRun:
    row = WorkflowRun(
        tenant_id=data.tenant_id,
        workflow_name=data.workflow_name,
        n8n_execution_id=data.n8n_execution_id,
        status=data.status,
        error_message=data.error_message,
        payload=data.payload,
    )
    db.add(row)
    return row