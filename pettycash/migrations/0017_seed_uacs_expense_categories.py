from django.db import migrations, transaction


UACS_EXPENSE_CATEGORIES = [
    (
        "2020101000",
        "Due to BIR",
        "Liability account for withholding of taxes payable/remittable to the Bureau of Internal Revenue. SSP reference only, if applicable.",
        [],
        ["Due to BIR"],
    ),
    (
        "5020101000",
        "Traveling Expenses - Local",
        "Local travel, fare, and transportation expenses incurred in official business. SSP reference only, if applicable.",
        ["3"],
        [
            "Traveling Expenses-Local",
            "Traveling Expenses - Local",
            "Fare/Transportation Expenses",
            "Fare and Transportation Expenses",
        ],
    ),
    (
        "5020301000",
        "Office Supplies Expenses",
        "Cost or value of office supplies issued to end-users for government operations. SSP reference only, if applicable.",
        ["8"],
        ["Office Supplies Expenses"],
    ),
    (
        "5020302000",
        "Accountable Forms Expenses",
        "Cost of accountable forms with or without money value issued to end-users. SSP reference only, if applicable.",
        [],
        ["Accountable Forms Expenses"],
    ),
    (
        "5020309000",
        "Fuel, Oil and Lubricants Expenses",
        "Fuel, oil, grease, and lubricant expenses for official operations and equipment. SSP reference only, if applicable.",
        ["4"],
        ["Fuel, Oil and Lubricants Expenses"],
    ),
    (
        "5020399000",
        "Other Supplies and Materials Expenses",
        "Supplies and materials consumed in operations not falling under a more specific supplies account. SSP reference only, if applicable.",
        ["12"],
        [
            "Other Supplies & Materials Expenses",
            "Other Supplies and Materials Expenses",
        ],
    ),
    (
        "5020401000",
        "Water Expenses",
        "Utility expense for water consumption and related water service charges. SSP reference only, if applicable.",
        ["18"],
        ["Water Expense", "Water expenses", "Water Expenses"],
    ),
    (
        "5020501000",
        "Postage and Courier Services",
        "Postage, courier, mailing, and related delivery service expenses. SSP reference only, if applicable.",
        ["13"],
        [
            "Postage & Courier Services",
            "Postage and Courier Services",
            "Postage and Courier Expenses",
        ],
    ),
    (
        "5020503000",
        "Internet Subscription Expenses",
        "Communication expense for internet connectivity and subscription services. SSP reference only, if applicable.",
        ["5"],
        ["Internet Expenses", "Internet Subscription Expenses"],
    ),
    (
        "5029902000",
        "Printing and Publication Expenses",
        "Printing, reproduction, publication, and related official document production expenses.",
        ["14"],
        ["Printing and Publication Expenses"],
    ),
    (
        "5029903000",
        "Representation Expenses",
        "Representation expenses incurred for official government functions and authorized activities.",
        ["16"],
        ["Representation Expenses"],
    ),
    (
        "5021199000",
        "Other Professional Services",
        "Professional service expenses not classified under a more specific professional service account. SSP reference only, if applicable.",
        ["11"],
        [
            "Other Professional Expenses",
            "Other Professional Services",
        ],
    ),
    (
        "5021299000",
        "Other General Services",
        "Cost of other general services contracted by the agency not otherwise classified under specific general services accounts. SSP reference only, if applicable.",
        [],
        ["Other General Services"],
    ),
    (
        "5010210000",
        "Honoraria",
        "Honoraria account. SSP reference only, if applicable.",
        [],
        ["Honoria", "Honoraria"],
    ),
    (
        "5021306000",
        "Repairs and Maintenance - Transportation Equipment",
        "Repairs and maintenance expenses for transportation equipment. SSP reference only, if applicable.",
        ["15", "5021306001"],
        [
            "Repairs & Maintenance-Transportation Equipment",
            "Repairs and Maintenance-Transportation Equipment",
            "Repairs and Maintenance - Transportation Equipment",
            "Repairs and Maintenance-Transportation Equipment- Motor Vehicle",
            "Repairs and Maintenance - Transportation Equipment - Motor Vehicle",
            "Repairs and Maintenance-Transportation Equipment- Motor Vehicles",
        ],
    ),
    (
        "5021501000",
        "Taxes, Duties and Licenses",
        "Taxes, duties, licenses, permits, and similar fees payable by the agency. SSP reference only, if applicable.",
        ["17"],
        [
            "Taxes, Duties & Licenses",
            "Taxes, Duties and Licenses",
        ],
    ),
    (
        "5021502000",
        "Fidelity Bond Premiums",
        "Fidelity bond premiums and related authorized bonding expenses. SSP reference only, if applicable.",
        [],
        ["Fidelity Bond Premiums"],
    ),
    (
        "5030104000",
        "Bank Charges",
        "Financial expenses for bank service charges and transaction fees. SSP reference only, if applicable.",
        ["1"],
        ["Bank Charges"],
    ),
    (
        "5050105000",
        "Depreciation - Machinery and Equipment",
        "Non-cash depreciation expense for machinery and equipment. SSP reference only, if applicable.",
        [],
        [
            "Depreciation- Machinery & Equipment",
            "Depreciation - Machinery and Equipment",
            "Depreciation-Machinery and Equipment",
        ],
    ),
    (
        "5029999000",
        "Other Maintenance and Operating Expenses",
        "Other maintenance and operating expenses not classified under a more specific MOOE account. SSP reference only, if applicable.",
        ["9", "10", "5029999002"],
        [
            "Other Maintenance & Operating Expenses",
            "Other Maintenance and Operating Expenses",
            "Other MOOE Expenses",
            "Other Disbursements",
        ],
    ),
]


LEGACY_CODES_TO_DEACTIVATE = {
    "2",
    "7",
    "5020502001",
    "5029904000",
}

LEGACY_NAMES_TO_DEACTIVATE = {
    "Communication Expenses - Mobile",
    "Telephone Expenses - Mobile",
    "Motor Vehicle Expenses",
    "Transportation and Delivery Expenses",
}


def normalize(value):
    return " ".join(
        (value or "")
        .replace("&", "and")
        .replace("–", "-")
        .replace("—", "-")
        .replace("-", " ")
        .lower()
        .split()
    )


def trim_to_field_max_length(instance, field_name, value):
    field = instance._meta.get_field(field_name)
    max_length = getattr(field, "max_length", None)

    if max_length and value and len(value) > max_length:
        return value[:max_length]

    return value


def save_instance(instance, using, update_fields=None):
    if update_fields:
        valid_fields = {field.name for field in instance._meta.fields}
        update_fields = [field for field in update_fields if field in valid_fields]
        instance.save(using=using, update_fields=update_fields)
    else:
        instance.save(using=using)


def archive_category(category, using):
    """
    Keep historical records safe by not deleting old categories.
    The old category is renamed as LEGACY and made inactive.
    """
    category.code = trim_to_field_max_length(
        category,
        "code",
        f"LEGACY-{category.pk}",
    )

    if "(Legacy" not in category.name:
        legacy_name = f"{category.name} (Legacy {category.pk})"
        category.name = trim_to_field_max_length(category, "name", legacy_name)

    category.is_active = False

    save_instance(
        category,
        using=using,
        update_fields=["code", "name", "is_active"],
    )


def seed_updated_uacs_expense_categories(apps, schema_editor):
    db_alias = schema_editor.connection.alias

    Entity = apps.get_model("users", "Entity")
    ExpenseCategory = apps.get_model("pettycash", "ExpenseCategory")
    PettyCashVoucher = apps.get_model("pettycash", "PettyCashVoucher")

    active_codes = {row[0] for row in UACS_EXPENSE_CATEGORIES}

    normalized_legacy_names_to_deactivate = {
        normalize(name) for name in LEGACY_NAMES_TO_DEACTIVATE
    }

    with transaction.atomic(using=db_alias):
        for entity in Entity.objects.using(db_alias).all():
            used_ids = set()

            for code, name, description, legacy_codes, aliases in UACS_EXPENSE_CATEGORIES:
                normalized_names = {normalize(name)}
                normalized_names.update(normalize(alias) for alias in aliases)

                existing_categories = list(
                    ExpenseCategory.objects.using(db_alias)
                    .filter(entity=entity)
                    .order_by("id")
                )

                target = (
                    ExpenseCategory.objects.using(db_alias)
                    .filter(entity=entity, code=code)
                    .order_by("id")
                    .first()
                )

                matched_categories = []

                for category in existing_categories:
                    if category.id in used_ids:
                        continue

                    if (
                        category.code == code
                        or category.code in legacy_codes
                        or normalize(category.name) in normalized_names
                    ):
                        matched_categories.append(category)

                if target:
                    category = target
                elif matched_categories:
                    category = matched_categories[0]
                else:
                    category = ExpenseCategory(entity=entity)

                category.code = code
                category.name = name
                category.description = description
                category.is_active = True
                save_instance(category, using=db_alias)

                used_ids.add(category.id)

                for old_category in matched_categories:
                    if old_category.pk == category.pk:
                        continue

                    PettyCashVoucher.objects.using(db_alias).filter(
                        expense_category=old_category
                    ).update(expense_category=category)

                    archive_category(old_category, using=db_alias)
                    used_ids.add(old_category.id)

            old_categories = (
                ExpenseCategory.objects.using(db_alias)
                .filter(entity=entity, is_active=True)
                .exclude(code__in=active_codes)
            )

            for old_category in old_categories:
                if (
                    old_category.code in LEGACY_CODES_TO_DEACTIVATE
                    or normalize(old_category.name) in normalized_legacy_names_to_deactivate
                ):
                    archive_category(old_category, using=db_alias)


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("pettycash", "0016_expensecategory_description"),
    ]

    operations = [
        migrations.RunPython(
            seed_updated_uacs_expense_categories,
            migrations.RunPython.noop,
        ),
    ]