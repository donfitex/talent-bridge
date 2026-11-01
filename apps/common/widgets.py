from django import forms


class RichTextWidget(forms.Textarea):
    def __init__(self, attrs=None):
        super().__init__({"data-rich-text": "true", **(attrs or {})})

    class Media:
        css = {"all": ["css/quill.snow.css", "css/editor.css"]}
        js = ["js/rich-editor.js"]
