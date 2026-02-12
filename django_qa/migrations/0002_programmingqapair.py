from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("django_qa", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProgrammingQAPair",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("question_id", models.BigIntegerField(db_index=True)),
                ("answer_id", models.BigIntegerField(db_index=True)),
                ("title", models.TextField(blank=True, default="")),
                ("question_body", models.TextField(blank=True, default="")),
                ("answer_body", models.TextField(blank=True, default="")),
                ("tags_json", models.JSONField(blank=True, default=list)),
                ("question_score", models.IntegerField(db_index=True, default=0)),
                ("answer_score", models.IntegerField(db_index=True, default=0)),
                ("view_count", models.IntegerField(blank=True, null=True)),
                ("question_creation_date", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("answer_creation_date", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("question_code_snippets_json", models.JSONField(blank=True, default=list)),
                ("answer_code_snippets_json", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "ordering": ["-answer_score", "-id"],
            },
        ),
        migrations.AddConstraint(
            model_name="programmingqapair",
            constraint=models.UniqueConstraint(fields=("question_id", "answer_id"), name="uniq_qa_pair_question_answer"),
        ),
    ]

