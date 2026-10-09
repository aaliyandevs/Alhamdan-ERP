import frappe

# Being listed in an HD Team is not enough: Helpdesk only lets someone work tickets once an
# HD Agent record exists (creating it also grants the "Agent" role).
AGENTS = ["usmanzubairkhan9@gmail.com", "mohammadahmedhanfi@gmail.com"]


def run():
	for user in AGENTS:
		if frappe.db.exists("HD Agent", user):
			continue
		name = frappe.db.get_value("User", user, "full_name")
		frappe.get_doc({"doctype": "HD Agent", "user": user, "agent_name": name}).insert(ignore_permissions=True)
		print("created HD Agent", user)
	frappe.db.commit()
	for user in AGENTS:
		print(user, "has Agent role:", "Agent" in frappe.get_roles(user))
	print("DONE")
