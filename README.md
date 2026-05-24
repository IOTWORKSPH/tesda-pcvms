# TESDA PCVMS

TESDA PCVMS is a Django-based Petty Cash Voucher Management System built for entity-level petty cash control, voucher processing, replenishment tracking, inspection and acceptance, supply documentation, and management oversight.

The system is designed around real operating roles: staff create and track petty cash requests, entity heads review and approve, custodians manage fund movement and replenishment, inspection teams verify purchased items, and supply officers issue and monitor IAR records. It provides a premium, mobile-friendly interface for day-to-day users and a modern Django Unfold admin for system administration.

## Purpose

PCVMS helps TESDA offices manage petty cash with clearer accountability, faster document preparation, better monitoring, and fewer manual tracking gaps.

It centralizes:

- Petty Cash Voucher creation and approval
- Cash advance release and liquidation
- Reimbursement processing
- Inspection and Acceptance Report support
- Purchased item registry
- Replenishment package preparation
- Fund ledger monitoring
- Expense analytics by category and staff
- Printable PCV, PR, IAR, CNRR, PDF, and Excel bundles

## Core Capabilities

### Role-Based Workspaces

Each user sees tools based on assigned roles. Multi-role users can access each role dashboard from the sidebar while still landing on their default dashboard based on role priority.

Supported roles:

- `Staff`
- `Administrator` / Entity Head
- `Custodian`
- `Inspection`
- `Supply`
- Django superuser/admin

### Staff Workspace

Staff users can:

- Create cash advance requests
- Create reimbursement requests
- Track request status from draft to posting
- Liquidate released cash advances
- View active and replenished voucher archives
- Print PCV, PR, IAR, CNRR, and full document bundles
- Monitor personal total expenses and expenses by category

### Entity Head Dashboard

Entity Head users can:

- Review pending approvals
- Approve or reject vouchers
- Monitor released and unliquidated exposure
- View fund portfolio health
- Track entity-wide expense categories
- Compare staff/requester expenses
- Review voucher queues, aging signals, and audit activity

### Petty Cash Custodian Dashboard

Custodians can:

- Initialize and manage petty cash funds
- Release approved cash advances
- Post approved reimbursements
- Monitor unliquidated cash advances
- Finalize or return liquidations
- View fund ledger activity
- Prepare, submit, release, and archive replenishment packages
- Monitor current, all, date-range, or replenishment-specific expenses

### Inspection and Acceptance Team

Inspection users can:

- Review pending inspection and acceptance items
- Monitor queue aging and document readiness
- View purchased item details across vouchers
- Open IAR documents from inspection work queues
- Trace items by PCV, requester, supplier, category, quantity, and amount

### Supply Officer Workspace

Supply users can:

- Monitor IAR issuance workload
- Generate IAR numbers using protected POST actions
- View purchased item registry
- Search by PCV, IAR, requester, supplier, or category
- Track requester/category mix and receiving activity

### Replenishment Management

The system supports the replenishment lifecycle:

- Draft replenishment package
- Submit to accounting
- Release replenishment with check details
- Track replenishment history
- View replenishment package details
- Print package PDFs
- Export Excel bundles
- Filter expense monitoring by current expenses, all expenses, date range, or specific replenishment report

### Document Generation

PCVMS supports printable and exportable documents:

- Petty Cash Voucher
- Purchase Request
- Inspection and Acceptance Report
- Certificate of Non-Receipt / Reimbursement-related document where applicable
- Full document bundle
- Replenishment package PDF
- Replenishment Excel bundle
- Voucher Excel export

Print actions are grouped into dropdown menus for a cleaner table experience.

## User Experience

The interface is built for repeated daily use:

- Responsive layouts for desktop and mobile
- Swipeable tables on smaller screens
- Mobile-safe modals and action menus
- Premium dashboard cards and comparison charts
- Role-specific sidebars
- Multi-role dashboard shortcuts
- Clear empty states and queue health indicators
- Filtered expense monitoring with labeled comparison bars
- Consistent action buttons and print dropdowns

## System Architecture

The project is organized as a modular Django application.

```text
tesda_pcvms/
├── audit/        # Audit trail models and admin
├── config/       # Django settings, URLs, WSGI/ASGI
├── core/         # Shared base models and middleware
├── finance/      # Fund clusters, responsibility centers, ledgers, funds
├── pettycash/    # Voucher, replenishment, supplier, item, and document workflows
├── reports/      # Reporting app placeholder/extension area
├── static/       # Static assets
├── templates/    # Shared and app-level templates
└── users/        # Custom user, entities, role dashboards, user management
```

## Technology Stack

- Python
- Django 6
- SQLite for local development
- PostgreSQL-compatible configuration through `DATABASE_URL`
- Django Unfold for the admin interface
- Bootstrap/AdminLTE-based application shell
- openpyxl for Excel document generation
- WeasyPrint support for PDF output
- WhiteNoise for static file serving
- django-environ for environment configuration

## Local Development

### 1. Create and Activate a Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` from the example file:

```powershell
copy .env.example .env
```

Recommended local defaults:

```env
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
TIME_ZONE=Asia/Manila
```

### 4. Run Migrations

```powershell
.\venv\Scripts\python.exe manage.py migrate
```

### 5. Create an Admin User

```powershell
.\venv\Scripts\python.exe manage.py createsuperuser
```

### 6. Start the Development Server

```powershell
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Open:

```text
http://127.0.0.1:8000/
```

## Admin Panel

The Django admin is available at:

```text
http://127.0.0.1:8000/admin/
```

The admin uses Django Unfold and includes organized navigation for:

- Users
- Groups and roles
- Entities
- Petty cash vouchers
- Expense categories
- Suppliers
- Petty cash funds
- Fund clusters
- Responsibility centers
- Ledger entries
- Audit logs

## Important Workflows

### Cash Advance

1. Staff creates a cash advance.
2. Entity Head reviews and approves.
3. Custodian releases cash.
4. Staff liquidates the cash advance.
5. Custodian reviews and finalizes liquidation.
6. Voucher becomes eligible for replenishment.

### Reimbursement

1. Staff creates a reimbursement request.
2. Entity Head reviews and approves.
3. Custodian posts reimbursement.
4. Voucher becomes eligible for replenishment.

### IAR and Purchased Items

1. Staff encodes purchase and item details.
2. Inspection team reviews purchased items.
3. Supply Officer issues or monitors IAR records.
4. Purchased items remain searchable in the registry.

### Replenishment

1. Custodian creates a replenishment package from eligible vouchers.
2. Package is submitted to accounting.
3. Released check details are encoded.
4. Records remain available for audit, PDF, and Excel export.

## Expense Monitoring

Dashboards include expense analytics for better management visibility.

Available filters:

- Current expenses, the default view
- All expenses
- Specific replenishment report
- Date range

Available comparisons:

- Expense categories
- Staff/requester expenses
- Personal staff expense categories

Current expenses exclude already replenished vouchers by default so users see what still affects the active petty cash cycle.

## Security and Controls

PCVMS includes:

- Role-based access checks
- Entity-level permission middleware
- CSRF protection
- Protected POST actions for state-changing operations
- Secure cookie settings through environment variables
- Security headers middleware
- Audit logging support
- Django password validators
- Admin access through Django authentication

For production, set:

```env
DEBUG=False
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## Deployment Checklist

Before deployment:

- Set a strong `SECRET_KEY`
- Set `DEBUG=False`
- Configure production `ALLOWED_HOSTS`
- Configure `CSRF_TRUSTED_ORIGINS`
- Use a production database
- Run migrations
- Run tests
- Collect static files
- Configure media storage and backups
- Configure HTTPS
- Review `docs/frontend_deployment_checklist.md`

Useful commands:

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test users pettycash
.\venv\Scripts\python.exe manage.py collectstatic
```

## Environment Variables

Key settings are configured in `.env`:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Enables/disables debug mode |
| `ALLOWED_HOSTS` | Allowed hostnames |
| `CSRF_TRUSTED_ORIGINS` | Trusted CSRF origins |
| `DATABASE_URL` | Database connection URL |
| `TIME_ZONE` | Application timezone |
| `EMAIL_BACKEND` | Email backend |
| `SESSION_COOKIE_SECURE` | Secure session cookie flag |
| `CSRF_COOKIE_SECURE` | Secure CSRF cookie flag |
| `SECURE_SSL_REDIRECT` | Force HTTPS |
| `WEASYPRINT_ENABLED` | Enables WeasyPrint PDF support where configured |

## Data Model Overview

Core records include:

- `Entity`
- `User`
- `PettyCashFund`
- `LedgerEntry`
- `Supplier`
- `ExpenseCategory`
- `PettyCashVoucher`
- `PCVItem`
- `ReceiptAttachment`
- `Replenishment`
- `Notification`
- `AuditLog`

## Quality Standards

The frontend has been tuned for:

- Responsive design readiness
- Mobile table scrolling
- Accessible labels and titles
- SEO essentials for app shell pages
- Security-oriented link and header behavior
- Consistent premium dashboard styling
- Reduced clutter in action columns

See:

```text
docs/frontend_deployment_checklist.md
```

## Project Status

PCVMS is actively developed for TESDA petty cash operations. The current version includes the complete role-based voucher workflow, modern dashboards, replenishment records, printable document packages, expense monitoring, and an upgraded Django admin experience.

## License

This repository is intended for internal TESDA PCVMS development and deployment. Add the appropriate organizational license before public distribution.
