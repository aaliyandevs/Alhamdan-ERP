import frappe

UNRESTRICTED = ["usmanzubairkhan9@gmail.com", "syedameenulhassanhamdani786@gmail.com"]


def run():
	for row in frappe.get_all("User Permission", fields=["name", "user", "allow", "for_value"]):
		print(row)
	for user in UNRESTRICTED:
		for name in frappe.get_all("User Permission", filters={"user": user, "allow": "Employee"}, pluck="name"):
			frappe.delete_doc("User Permission", name, ignore_permissions=True)
			print("deleted employee restriction for", user)
		if user.startswith("syedameen"):
			for name in frappe.get_all("User Permission", filters={"user": user, "allow": "Company"}, pluck="name"):
				frappe.delete_doc("User Permission", name, ignore_permissions=True)
				print("deleted company restriction for", user)
		emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
		if emp:
			frappe.db.set_value("Employee", emp, "create_user_permission", 0)
	frappe.db.commit()
	print("DONE")
