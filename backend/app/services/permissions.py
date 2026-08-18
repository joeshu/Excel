ROLE_PERMISSIONS = {
    "admin": {"template_manage", "workflow_edit", "workflow_run", "result_download", "audit_read"},
    "operator": {"workflow_run", "result_download", "audit_read"},
    "viewer": {"audit_read"},
}


def can(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
