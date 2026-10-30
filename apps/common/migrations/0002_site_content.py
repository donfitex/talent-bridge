from django.db import migrations


def seed(apps, schema_editor):
    content = apps.get_model("common", "SiteContent")
    for key, title, body in [
        ("contact", "Contact us", "Need help with your account, a job application or hiring? Send our team a message."),
        ("home", "Good work. Great possibilities.", "Discover opportunities and connect with teams that value your skills."),
    ]:
        content.objects.using(schema_editor.connection.alias).get_or_create(key=key, defaults={"title": title, "body": body})


class Migration(migrations.Migration):
    dependencies = [("common", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
