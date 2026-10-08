import frappe

# Mirrors the role taxonomy table in the approved plan, as reusable bundles
# so onboarding a new hire is "assign one Role Profile", not re-deriving roles.
ROLE_PROFILES = {
	"Group Admin": ["System Manager", "Accounts Manager"],
	"Group Finance": ["Accounts Manager", "Accounts User"],
	"Group HR": ["HR Manager", "Employee"],
	"Infiqo - Sales/Accounts": ["Sales User", "Accounts User"],
	"Infiqo - Delivery": ["Projects User"],
	"Infiqo - Support": ["Agent"],
	"Uroojj - Fulfillment": ["Stock User"],
	"Uroojj - Customer Service": ["Sales User", "Agent"],
}


def run():
	for name, roles in ROLE_PROFILES.items():
		if frappe.db.exists("Role Profile", name):
			continue
		doc = frappe.get_doc({"doctype": "Role Profile", "role_profile": name})
		for role in roles:
			if not frappe.db.exists("Role", role):
				print("skipped missing role:", role, "(not installed)")
				continue
			doc.append("roles", {"role": role})
		doc.insert(ignore_permissions=True)
		print("created role profile", name)
	frappe.db.commit()
	print("DONE")
