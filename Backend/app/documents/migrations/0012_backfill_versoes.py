"""
Renumerada de 0007 para 0012 após merge.

Data migration: cria uma versão inicial (v1, ativa) para cada Documento existente
e vincula todos os chunks atuais a essa versão. Idempotente.
"""
from django.db import migrations


def backfill(apps, schema_editor):
    documento_model = apps.get_model("documents", "Documento")
    versao_model = apps.get_model("documents", "VersaoDocumento")
    chunk_model = apps.get_model("documents", "ChunkDocumento")

    for doc in documento_model.objects.all():
        if doc.versoes.exists():
            continue
        v1 = versao_model.objects.create(
            documento=doc,
            numero=1,
            nome=doc.nome,
            tipo=doc.tipo,
            caminho_arquivo=doc.caminho_arquivo,
            ativa=True,
        )
        chunk_model.objects.filter(documento=doc, versao__isnull=True).update(versao=v1)


def reverse(apps, schema_editor):
    # Backfill é idempotente e seguro; reverter dados existentes apagaria
    # versões/links criados por outras migrações posteriores, então o reverso é no-op.
    return


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0011_versaodocumento"),
    ]

    operations = [
        migrations.RunPython(backfill, reverse),
    ]
