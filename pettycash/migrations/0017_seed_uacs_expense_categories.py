from django.db import migrations


UACS_EXPENSE_CATEGORIES = [
    ("5030104000", "Bank Charges", "Financial expenses for bank service charges and transaction fees.", ["1"], ["Bank Charges"]),
    ("5020502001", "Telephone Expenses - Mobile", "Communication expense for mobile phone call, text, and related mobile service charges.", ["2"], ["Communication Expenses - Mobile"]),
    ("5020101000", "Traveling Expenses - Local", "Local travel, fare, and transportation expenses incurred in official business.", ["3"], ["Fare/Transportation Expenses"]),
    ("5020309000", "Fuel, Oil and Lubricants Expenses", "Fuel, oil, grease, and lubricant expenses for official operations and equipment.", ["4"], ["Fuel, Oil and Lubricants Expenses"]),
    ("5020503000", "Internet Subscription Expenses", "Communication expense for internet connectivity and subscription services.", ["5"], ["Internet Expenses"]),
    ("5021601000", "Labor and Wages", "Payments for labor and wage services chargeable to maintenance and operating expenses.", ["6"], ["Labor and Wages"]),
    ("5029904000", "Transportation and Delivery Expenses", "Transportation, delivery, freight, hauling, and similar operating expenses.", ["7"], ["Motor Vehicle Expenses"]),
    ("5020301000", "Office Supplies Expenses", "Office supplies consumed in regular government operations.", ["8"], ["Office Supplies Expenses"]),
    ("5029999000", "Other Maintenance and Operating Expenses", "Other MOOE items not classified under a more specific UACS expense account.", ["9"], ["Other Disbursements"]),
    ("5029999002", "Other Maintenance and Operating Expenses", "Other maintenance and operating expenses not otherwise specifically classified.", ["10"], ["Other MOOE Expenses"]),
    ("5021199000", "Other Professional Services", "Professional service expenses not classified as legal, auditing, or consultancy services.", ["11"], ["Other Professional Expenses", "Other Professional Services"]),
    ("5020399000", "Other Supplies and Materials Expenses", "Supplies and materials consumed in operations that do not fall under a specific supplies account.", ["12"], ["Other Supplies and Materials Expenses"]),
    ("5020501000", "Postage and Courier Expenses", "Postage, courier, mailing, and delivery service expenses.", ["13"], ["Postage and Courier Expenses"]),
    ("5029902000", "Printing and Publication Expenses", "Printing, reproduction, publication, and related official document production expenses.", ["14"], ["Printing and Publication Expenses"]),
    ("5021306001", "Repairs and Maintenance - Transportation Equipment - Motor Vehicles", "Repairs and maintenance expenses for official motor vehicles.", ["15"], ["Repairs and Maintenance-Transportation Equipment- Motor Vehicle", "Repairs and Maintenance - Transportation Equipment - Motor Vehicle"]),
    ("5029903000", "Representation Expenses", "Representation expenses incurred for official government functions and authorized activities.", ["16"], ["Representation Expenses"]),
    ("5021501000", "Taxes, Duties and Licenses", "Taxes, duties, licenses, permits, and similar fees payable by the agency.", ["17"], ["Taxes, Duties & Licenses", "Taxes, Duties and Licenses"]),
    ("5020401000", "Water Expenses", "Utility expense for water consumption and related water service charges.", ["18"], ["Water expenses", "Water Expenses"]),
]


def normalize(value):
    return " ".join((value or "").replace("&", "and").replace("-", " ").lower().split())


def seed_uacs_expense_categories(apps, schema_editor):
    Entity = apps.get_model("users", "Entity")
    ExpenseCategory = apps.get_model("pettycash", "ExpenseCategory")
    PettyCashVoucher = apps.get_model("pettycash", "PettyCashVoucher")

    for entity in Entity.objects.all():
        used_ids = set()

        for code, name, description, legacy_codes, aliases in UACS_EXPENSE_CATEGORIES:
            normalized_names = {normalize(name)}
            normalized_names.update(normalize(alias) for alias in aliases)

            existing = list(ExpenseCategory.objects.filter(entity=entity).order_by("id"))
            target = ExpenseCategory.objects.filter(entity=entity, code=code).first()
            source = None

            for category in existing:
                if category.id in used_ids:
                    continue

                if (
                    category.code == code
                    or category.code in legacy_codes
                    or normalize(category.name) in normalized_names
                ):
                    source = category
                    break

            if target and source and target.pk != source.pk:
                PettyCashVoucher.objects.filter(expense_category=source).update(expense_category=target)
                source.code = f"LEGACY-{source.pk}"
                source.name = f"{source.name} (Legacy)"
                source.is_active = False
                source.save(update_fields=["code", "name", "is_active", "updated_at"])
                category = target
            elif source:
                category = source
            elif target:
                category = target
            else:
                category = ExpenseCategory(entity=entity)

            category.code = code
            category.name = name
            category.description = description
            category.is_active = True
            category.save()
            used_ids.add(category.id)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("pettycash", "0016_expensecategory_description"),
    ]

    operations = [
        migrations.RunPython(seed_uacs_expense_categories, migrations.RunPython.noop),
    ]
