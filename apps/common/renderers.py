from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = (renderer_context or {}).get("response")
        if response and response.status_code < 400 and data is not None:
            if not isinstance(data, dict) or "data" not in data:
                data = {"data": data}
        return super().render(data, accepted_media_type, renderer_context)
