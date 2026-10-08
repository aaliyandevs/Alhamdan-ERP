import importlib

# Order matters: each module may depend on records created by an earlier one.
# Every module is idempotent, so re-running on an existing site is safe.
#
#   bench --site <site> execute alhamdan_erp.setup.run_all.run
MODULES = [
	"seed_foundation",  # masters, companies, fiscal years, setup-complete flags
	"seed_people_items",  # users, Uroojj items, Nooria Travels customer
	"seed_finance",  # exchange rates, price lists, tax templates, Uroojj warehouses
	"seed_item_defaults",  # default warehouse per Uroojj item
	"seed_hr",  # holiday list, leave policy, employees
	"apply_corrections",  # cross-company access, Yasir, joining dates, leave assignments
	"fix_employee_perms",  # drop auto-created restrictions for HR manager / admins
	"seed_infiqo_pipeline",  # CRM stages + Project Template
	"fix_crm_order",  # Infiqo stages first, then Won/Lost, CRM built-ins last
	"seed_uroojj_manufacturing",  # operations, workstations, QC template
	"seed_helpdesk_teams",
	"seed_billing_architecture",  # service-scope custom fields, payment terms
	"seed_accounts_settings",
	"seed_payment_modes",  # Cash accounts per company, Uroojj COD
	"seed_role_profiles",
	"seed_letterheads",
	"seed_naming_rules",
]


def run():
	for name in MODULES:
		print(f"=== {name} ===")
		module = importlib.import_module(f"alhamdan_erp.setup.{name}")
		module.run()
	print("ALL DONE")
