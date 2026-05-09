from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pettycash", "0015_pettycashvoucher_has_cnrr"),
    ]

    operations = [
        migrations.AddField(
            model_name="expensecategory",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="expensecategory",
            name="code",
            field=models.CharField(max_length=50, verbose_name="UACS Code"),
        ),
        migrations.AlterField(
            model_name="expensecategory",
            name="name",
            field=models.CharField(max_length=150, verbose_name="Category"),
        ),
        migrations.AlterModelOptions(
            name="expensecategory",
            options={"ordering": ["code", "name"]},
        ),
    ]
