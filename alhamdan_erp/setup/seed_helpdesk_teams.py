import frappe

# Placeholder members until the user says who actually staffs support/CS day-to-day.
TEAMS = {
	"Infiqo Support": ["usmanzubairkhan9@gmail.com"],
	"Uroojj Customer Service": ["mohammadahmedhanfi@gmail.com"],
}


def run():
	for team, users in TEAMS.items():
		if frappe.db.exists("HD Team", team):
			continue
		doc = frappe.get_doc({"doctype": "HD Team", "team_name": team})
		for u in users:
			doc.append("users", {"user": u})
		doc.insert(ignore_permissions=True)
		print("created HD team", team, "with", users)
	frappe.db.commit()
	print("DONE")
