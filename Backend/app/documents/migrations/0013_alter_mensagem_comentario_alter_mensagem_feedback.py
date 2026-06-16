from django.db import migrations


def backfill_vazios(apps, schema_editor):
    """Converte NULL -> '' em feedback/comentario antes de torna-los NOT NULL.

    Precisa rodar numa migracao separada do AlterField: no PostgreSQL nao se
    pode alterar a coluna para NOT NULL na mesma transacao que fez o UPDATE
    dos dados ("pending trigger events").
    """
    mensagem_model = apps.get_model("documents", "Mensagem")
    mensagem_model.objects.filter(feedback__isnull=True).update(feedback="")
    mensagem_model.objects.filter(comentario__isnull=True).update(comentario="")


def reverse_noop(apps, schema_editor):
    # '' e um valor valido; nao ha necessidade de reverter para NULL.
    return


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0012_backfill_versoes'),
    ]

    operations = [
        migrations.RunPython(backfill_vazios, reverse_noop),
    ]
