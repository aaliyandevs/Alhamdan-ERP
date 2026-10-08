import frappe

USERS = [
	("syedameenulhassanhamdani786@gmail.com", "Syed Ameen Ul Hassan Hamdani", ["System Manager", "Accounts Manager"], []),
	("mabdullahazizawan@gmail.com", "Abdullah Aziz", ["Sales Manager", "Projects Manager", "Accounts User"], ["Infiqo"]),
	("aaliyan.devs@gmail.com", "Aaliyan Irfan", ["Projects User"], ["Infiqo"]),
	("arifsabzali6@gmail.com", "Arif Ali", ["Projects User"], ["Infiqo"]),
	("usmanzubairkhan9@gmail.com", "Usman", ["HR Manager", "Projects User"], ["Infiqo"]),
	("mohammadahmedhanfi@gmail.com", "Ahmed", ["Sales User"], ["Infiqo"]),
]

SKUS = [
	("Berry Aura", 2699),
	("Storm Legend", 2999),
	("Corporate Authority", 3099),
	("Black Dominion", 3099),
	("Velvet Pour", 3599),
]


def run():
	for email, first_name, roles, companies in USERS:
		if not frappe.db.exists("User", email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first_name,
					"send_welcome_email": 0,
					"enabled": 1,
					"user_type": "System User",
				}
			).insert(ignore_permissions=True)
			print("created user", email)
		user = frappe.get_doc("User", email)
		have = {r.role for r in user.roles}
		for role in roles:
			if role not in have:
				user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
		for company in companies:
			if not frappe.db.exists("User Permission", {"user": email, "allow": "Company", "for_value": company}):
				frappe.get_doc(
					{"doctype": "User Permission", "user": email, "allow": "Company", "for_value": company}
				).insert(ignore_permissions=True)
				print("restricted", email, "->", company)

	if not frappe.db.exists("Item Group", "Fragrances"):
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": "Fragrances",
				"parent_item_group": "All Item Groups",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)

	for name, price in SKUS:
		code = "URJ-" + name.upper().replace(" ", "-")
		if frappe.db.exists("Item", code):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": name,
				"item_group": "Fragrances",
				"stock_uom": "Nos",
				"is_stock_item": 1,
				"description": f"{name} - Eau de Parfum",
				"standard_rate": price,
			}
		).insert(ignore_permissions=True)
		print("created item", code, price)

	if not frappe.db.exists("Customer", "Nooria Travels"):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": "Nooria Travels",
				"customer_type": "Company",
				"customer_group": "Commercial",
				"territory": "Pakistan",
			}
		).insert(ignore_permissions=True)
		print("created customer Nooria Travels")

	frappe.db.commit()
	print("DONE")
