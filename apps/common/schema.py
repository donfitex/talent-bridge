def envelope_responses(result, generator, request, public):
    """Document the JSON renderer's success envelope for every API operation."""
    for path in result.get("paths", {}).values():
        for operation in path.values():
            if not isinstance(operation, dict):
                continue
            for code, response in operation.get("responses", {}).items():
                if not str(code).startswith("2"):
                    continue
                media = response.get("content", {}).get("application/json")
                if media and "schema" in media:
                    media["schema"] = {
                        "type": "object",
                        "required": ["data"],
                        "properties": {"data": media["schema"], "message": {"type": "string"}},
                    }
    return result
