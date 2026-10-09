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
	"seed_helpdesk_agents",  # HD Agent records (grants the Agent role)
	"seed_billing_architecture",  # service-scope custom fields, payment terms
	"seed_infiqo_service_item",  # generic Custom Service item for Infiqo
	"fix_company_defaults",  # default accounts, 50/50 due dates, scheduler
	"seed_accounts_settings",
	"seed_payment_modes",  # Cash accounts per company, Uroojj COD
	"seed_role_profiles",
	"seed_letterheads",
	"seed_naming_rules",
	"fix_functional_defects",  # currency default, HR holiday assignment, QC, roles
	"branding",  # white-label names, hide unused modules
	"company_home",  # Home = 3 company tiles, each with its own sidebar
]


def run():
	for name in MODULES:
		print(f"=== {name} ===")
		module = importlib.import_module(f"alhamdan_erp.setup.{name}")
		module.run()
	print("ALL DONE")
