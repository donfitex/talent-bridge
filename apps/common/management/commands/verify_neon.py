"""Exercise real database/storage integrations without retaining synthetic users."""

import secrets
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from rest_framework.test import APIClient

from apps.resumes.models import Resume
from apps.users.models import User


class Command(BaseCommand):
    help = "Verify Neon database persistence and private CV upload/download through the API."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql" or settings.RESUME_STORAGE_BACKEND != "neon":
            raise CommandError("This verification requires PostgreSQL and Neon resume storage.")
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            database = cursor.fetchone()[0]
        self.stdout.write(f"PASS: PostgreSQL connection to {database}")
        payload = b"%PDF-1.4\nTalentBridge Neon CV verification\n%%EOF\n"
        stored_name = None
        storage = None
        try:
            with transaction.atomic():
                counter = f"neon-verification:{uuid.uuid4().hex}"
                cache.add(counter, 0, timeout=30)
                if cache.incr(counter) != 1:
                    raise CommandError("Shared cache counter verification failed.")
                self.stdout.write("PASS: shared database-backed cache counter")
                user = User.objects.create_user(
                    f"neon-smoke-{uuid.uuid4().hex}@example.invalid", secrets.token_urlsafe(32)
                )
                client = APIClient()
                client.force_authenticate(user)
                response = client.post(
                    "/api/v1/resumes/",
                    {
                        "title": "Neon verification CV",
                        "file": SimpleUploadedFile(
                            "neon-verification.pdf", payload, content_type="application/pdf"
                        ),
                    },
                    format="multipart",
                    HTTP_HOST="localhost",
                )
                if response.status_code != 201:
                    raise CommandError(f"CV upload failed: HTTP {response.status_code}")
                resume = Resume.objects.get(pk=response.data["data"]["id"])
                stored_name, storage = resume.file.name, resume.file.storage
                response = client.get(
                    f"/api/v1/resumes/{resume.pk}/download/", HTTP_HOST="localhost"
                )
                if response.status_code != 200:
                    raise CommandError(f"CV download failed: HTTP {response.status_code}")
                # Django test streaming wrappers close the response safely on exhaustion.
                downloaded = b"".join(response.streaming_content)
                if downloaded != payload:
                    raise CommandError("CV read-back differs from uploaded bytes.")
                self.stdout.write(
                    f"PASS: CV upload HTTP 201; authorized download HTTP 200; {len(downloaded)} bytes match"
                )
                outsider = User.objects.create_user(
                    f"neon-outsider-{uuid.uuid4().hex}@example.invalid"
                )
                client.force_authenticate(outsider)
                response = client.get(
                    f"/api/v1/resumes/{resume.pk}/download/", HTTP_HOST="localhost"
                )
                if response.status_code != 403:
                    raise CommandError("Private CV ownership protection failed.")
                self.stdout.write("PASS: another candidate cannot download the CV (HTTP 403)")
                transaction.set_rollback(True)
        finally:
            if storage is not None and stored_name is not None:
                storage.delete(stored_name)
        self.stdout.write("PASS: synthetic users rolled back and this verification CV removed")
