"""
Renumerada de 0007 para 0012 após merge.

Data migration: cria uma versão inicial (v1, ativa) para cada Documento existente
e vincula todos os chunks atuais a essa versão. Idempotente.
"""
from django.db import migrations


def backfill(apps, schema_editor):
    Documento = apps.get_model("documents", "Documento")
    VersaoDocumento = apps.get_model("documents", "VersaoDocumento")
    ChunkDocumento = apps.get_model("documents", "ChunkDocumento")

    for doc in Documento.objects.all():
        if doc.versoes.exists():
            continue
        v1 = VersaoDocumento.objects.create(
            documento=doc,
            numero=1,
            nome=doc.nome,
            tipo=doc.tipo,
            caminho_arquivo=doc.caminho_arquivo,
            ativa=True,
        )
        ChunkDocumento.objects.filter(documento=doc, versao__isnull=True).update(versao=v1)


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0011_versaodocumento"),
    ]

    operations = [
        migrations.RunPython(backfill, reverse),
    ]
