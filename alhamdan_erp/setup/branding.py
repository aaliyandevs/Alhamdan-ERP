import frappe

# White-labelling and menu clean-up, done purely through settings records (no changes to
# the Frappe/ERPNext/HRMS/CRM/Helpdesk code). Runs after every `bench migrate` (hooks.py)
# because Frappe re-syncs its standard desktop icons/workspaces on migrate.

ERP_NAME = "Alhamdan ERP"

# App tiles on the apps screen
RENAME_ICONS = {
	"ERPNext Settings": "Settings",
	"Framework": "Admin",
	"Frappe HR": "HR",
	"Frappe CRM": "Infiqo CRM",
	"Helpdesk": "Support Desk",
}

# Modules the group does not use. Hidden, not deleted: unhide any of them to bring it back.
HIDE = [
	"Welcome Workspace", "Tax & Benefits", "Performance", "Tenure", "Recruitment", "Subcontracting",
	"Assets", "Expenses", "Support", "CRM", "Website", "Share Management", "Subscription",
]


def apply():
	ws = frappe.get_single("Website Settings")
	ws.app_name = ERP_NAME
	ws.hide_footer_signup = 1
	ws.footer_powered = ""
	ws.save(ignore_permissions=True)

	nav = frappe.get_single("Navbar Settings")
	nav.help_dropdown = [r for r in nav.help_dropdown if r.item_label not in ("About", "Frappe Support")]
	nav.settings_dropdown = [r for r in nav.settings_dropdown if r.item_label != "Delete Demo Data"]
	nav.save(ignore_permissions=True)

	for old, new in RENAME_ICONS.items():
		if frappe.db.exists("Desktop Icon", old):
			frappe.db.set_value("Desktop Icon", old, "label", new)

	if frappe.db.exists("Desktop Icon", "ERPNext"):
		frappe.db.set_value("Desktop Icon", "ERPNext", {"label": "ERPNext", "hidden": 1})

	for label in HIDE:
		for name in frappe.get_all("Desktop Icon", filters={"label": label}, pluck="name"):
			frappe.db.set_value("Desktop Icon", name, "hidden", 1)
		for name in frappe.get_all("Workspace", filters={"title": label}, pluck="name"):
			frappe.db.set_value("Workspace", name, "is_hidden", 1)

	crm = frappe.get_single("FCRM Settings")
	crm.brand_name = "Infiqo CRM"
	crm.currency = "PKR"
	crm.persona_captured = 1
	crm.save(ignore_permissions=True)

	hd = frappe.get_single("HD Settings")
	hd.brand_name = "Alhamdan Support"
	hd.persona_captured = 1
	hd.save(ignore_permissions=True)

	frappe.db.set_single_value("System Settings", "enable_onboarding", 0)
	frappe.db.commit()
	frappe.clear_cache()


def run():
	apply()
	print("icons:", [(i.label, i.hidden) for i in frappe.get_all("Desktop Icon", fields=["label", "hidden"], filters={"icon_type": "App"})])
	print("hidden workspaces:", frappe.get_all("Workspace", filters={"is_hidden": 1}, pluck="title"))
	print("DONE")
