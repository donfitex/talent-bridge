from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateResumeStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.RESUME_STORAGE_DIR, base_url=None)

    def url(self, name):
        raise ValueError("Private resumes require an authorized download endpoint.")
