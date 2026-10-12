import frappe

# Mirrors the role taxonomy table in the approved plan, as reusable bundles
# so onboarding a new hire is "assign one Role Profile", not re-deriving roles.
#
# Gotcha: once a User has any Role Profile assigned, User.validate() calls
# populate_role_profile_roles() on EVERY save, which REPLACES user.roles with
# exactly the union of its profiles' roles -- any role not listed in a profile
# gets silently stripped on the next save, even if added directly to the user.
# So "Employee" (every operational/admin user needs it) must be listed in
# every profile here, not bolted onto users afterward.
ROLE_PROFILES = {
	"Group Admin": ["System Manager", "Accounts Manager", "Employee"],
	"Group Finance": ["Accounts Manager", "Accounts User", "Employee"],
	"Group HR": ["HR Manager", "Employee"],
	"Infiqo - Sales/Accounts": ["Sales User", "Accounts User", "Employee"],
	"Infiqo - Manager": ["Sales Manager", "Projects Manager", "Accounts User", "Sales User", "Employee"],
	"Infiqo - Delivery": ["Projects User", "Employee"],
	"Uroojj - Fulfillment": ["Stock User", "Employee"],
	"Uroojj - Customer Service": ["Sales User", "Employee"],
}


def run():
	for name, roles in ROLE_PROFILES.items():
		doc = (
			frappe.get_doc("Role Profile", name)
			if frappe.db.exists("Role Profile", name)
			else frappe.get_doc({"doctype": "Role Profile", "role_profile": name})
		)
		have = {r.role for r in doc.roles}
		changed = doc.is_new()
		for role in roles:
			if role in have:
				continue
			if not frappe.db.exists("Role", role):
				print("skipped missing role:", role, "(not installed)")
				continue
			doc.append("roles", {"role": role})
			changed = True
		if doc.is_new():
			doc.insert(ignore_permissions=True)
			frappe.db.commit()  # commit per item: one bad doc shouldn't roll back everything before it
			print("created role profile", name)
		elif changed:
			doc.save(ignore_permissions=True)
			frappe.db.commit()
			print("updated role profile", name, "roles now:", sorted(r.role for r in doc.roles))
	print("DONE")
