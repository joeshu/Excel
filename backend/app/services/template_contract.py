def native_required_fields(profile: dict, column_mapping: dict[str, str]) -> list[str]:
    contract = profile.get("field_contract", {}) if profile else {}
    mapped_fields = [field for field in (column_mapping or {}).values() if field]
    required = contract.get("required_source_fields") or contract.get("required") or mapped_fields
    derived = set(contract.get("derived_template_fields") or [])
    return sorted({str(field) for field in required if field and field not in derived})


def validate_native_contract(profile: dict, column_mapping: dict[str, str], source_fields: set[str]) -> dict:
    required = native_required_fields(profile, column_mapping)
    missing = sorted(set(required) - source_fields)
    return {"valid": not missing, "required_fields": required, "missing_fields": missing, "matched_fields": sorted(set(required) & source_fields)}
