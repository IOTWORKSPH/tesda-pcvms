#pettycash urls.py codes
from django.urls import path
from . import views

app_name = "pettycash"

urlpatterns = [

    path("cash-advance/new/",views.create_cash_advance,name="create_cash_advance"),
    path("cash-advance/<uuid:uuid>/liquidate/",views.liquidate_cash_advance,name="liquidate_cash_advance"),
    path("my-vouchers/",views.my_vouchers,name="my_vouchers"),
    path("refund/new/",views.create_reimbursement,name="create_reimbursement"),
    path("pcv/<uuid:uuid>/",views.pcv_detail,name="pcv_detail"),

    path("notification/<int:pk>/",views.notification_redirect,name="notification_redirect"),
    path("notifications/mark-all/",views.mark_all_notifications_read,name="mark_all_notifications_read"),
    path("notifications/",views.notifications_list,name="notifications_list"),

    # Edit Draft (Unified)
    path("pcv/<uuid:uuid>/edit/",views.edit_pcv,name="edit_pcv"),
    path("pcv/delete/<uuid:uuid>/",views.delete_pcv,name="delete_pcv"),
    
    path("refund/<uuid:uuid>/submit/",views.submit_refund,name="submit_refund"),
    path("cash-advance/<uuid:uuid>/submit/",views.submit_cash_advance,name="submit_cash_advance"),

    path("ajax/suppliers/", views.supplier_autocomplete, name="supplier_autocomplete"),

    # Administrator Approve
    path("admin/bulk-approve/",views.bulk_approve,name="bulk_approve"),
    path("pcv/<uuid:uuid>/approve/",views.approve_voucher,name="approve_voucher"),
    path("pcv/<uuid:uuid>/reject/",views.reject_voucher,name="reject_voucher"),

    # ==========================
    # CUSTODIAN PAGES
    # ==========================
    path("fund/initialize/", views.create_initial_fund, name="create_initial_fund"),
    path("voucher/<int:pk>/release/", views.release_cash_view, name="release_cash"),
    path("voucher/<int:pk>/post-reimbursement/", views.post_reimbursement_view, name="post_reimbursement"),
    path("fund/release/",views.custodian_release_list,name="custodian_release_list"),
    path("fund/unliquidated/",views.custodian_unliquidated,name="custodian_unliquidated"),
    path("liquidation/finalize/<uuid:uuid>/",views.finalize_liquidation,name="finalize_liquidation"),
    path("liquidation/return/<uuid:uuid>/",views.return_liquidation,name="return_liquidation"),
    path("fund/ledger/",views.custodian_fund_ledger,name="custodian_fund_ledger"),
    
    
    # REPORTS
    path("reports/replenishment/", views.replenishment_report, name="replenishment_report"),
    path("reports/replenishment/generate/", views.replenishment_generate, name="replenishment_generate"),
    path("reports/replenishment/package/", views.replenishment_package_pdf, name="replenishment_package_pdf"),
    path("reports/replenishment/export/", views.replenishment_export_excel, name="replenishment_export_excel"),

    # ==========================
    # REPLENISHMENT MANAGEMENT
    # ==========================

    path("replenishment/", views.replenishment_list, name="replenishment_list"),
    path("replenishment/create/", views.create_replenishment, name="create_replenishment"),
    path("replenishment/<int:pk>/", views.replenishment_detail, name="replenishment_detail"),


    # ================= PRINT ROUTES =================
    path("print/pcv/<uuid:uuid>/", views.print_pcv, name="print_pcv"),
    path("print/pr/<uuid:uuid>/", views.print_pr, name="print_pr"),
    path("print/iar/<uuid:uuid>/", views.print_iar, name="print_iar"),
    path("print/all/<uuid:uuid>/", views.print_all, name="print_all"),

    # =============================
    # INSPECTION TEAM
    # =============================

    path("inspection/pending/", views.inspection_pending, name="inspection_pending"),
    path("inspection/items/", views.inspection_all_items, name="inspection_all_items"),

    # =============================
    # SUPPLY OFFICE
    # =============================

    path("supply/items/", views.supply_items, name="supply_items"),
    path("supply/iar-pending/", views.supply_iar_pending, name="supply_iar_pending"),
    path("supply/iar-generate/<uuid:uuid>/", views.generate_iar, name="generate_iar"),
]
