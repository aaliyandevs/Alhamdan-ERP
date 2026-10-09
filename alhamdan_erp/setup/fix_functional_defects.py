import frappe

# Defects found by running real transactions end to end (not by looking at records).

GROUP_ADMIN_ROLES = [
	"System Manager", "Accounts Manager", "Accounts User",
	"Sales Manager", "Sales User", "Sales Master Manager",
	"Purchase Manager", "Purchase User", "Purchase Master Manager",
	"Stock Manager", "Stock User", "Manufacturing Manager", "Manufacturing User",
	"Quality Manager", "Item Manager", "Projects Manager", "Projects User",
	"HR Manager", "HR User",
]
GROUP_ADMINS = ["syedameenulhassanhamdani786@gmail.com", "iamyasirmarwat@gmail.com"]
HOLIDAY_LIST = "Pakistan Holidays FY2026-27"


def add_roles(user, roles):
	doc = frappe.get_doc("User", user)
	have = {r.role for r in doc.roles}
	missing = [r for r in roles if r not in have and frappe.db.exists("Role", r)]
	if not missing:
		return
	for role in missing:
		doc.append("roles", {"role": role})
	doc.save(ignore_permissions=True)



def run():
	# The wizard normally replaces Frappe's factory default (INR). Left as INR, any document
	# without an explicit price list is created in INR and booked to the PKR ledger at ~2.87x.
	# Must go through .save(): Frappe mirrors these into a separate defaults table on save.
	gd = frappe.get_single("Global Defaults")
	gd.default_currency = "PKR"
	gd.save(ignore_permissions=True)
	ss = frappe.get_single("Selling Settings")
	ss.selling_price_list = "Standard Selling"
	ss.save(ignore_permissions=True)

	# Plan decision: no approval workflows in v1.
	frappe.db.set_single_value("HR Settings", "leave_approver_mandatory_in_leave_application", 0)
	frappe.db.set_single_value("HR Settings", "expense_approver_mandatory_in_expense_claim", 0)

	# HRMS v16 finds holidays through Holiday List Assignment, not the Employee/Company field.
	for company in ("Al Hamdan Enterprise", "Infiqo", "Uroojj"):
		if frappe.db.exists("Holiday List Assignment", {"applicable_for": "Company", "assigned_to": company, "holiday_list": HOLIDAY_LIST}):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Holiday List Assignment",
				"applicable_for": "Company",
				"assigned_to": company,
				"holiday_list": HOLIDAY_LIST,
				"from_date": "2026-07-01",
			}
		)
		doc.insert(ignore_permissions=True)
		if doc.meta.is_submittable:
			doc.submit()
		print("holiday list assigned to", company)

	# QC checks like "Fragrance Match" are pass/fail, not numbers.
	frappe.db.sql("update `tabItem Quality Inspection Parameter` set `numeric` = 0 where parent = %s", "Uroojj Finished Goods QC")

	# Roles: System Manager alone cannot create quotations, stock entries or items.
	for user in GROUP_ADMINS:
		add_roles(user, GROUP_ADMIN_ROLES)
	if frappe.db.exists("Role Profile", "Group Admin"):
		rp = frappe.get_doc("Role Profile", "Group Admin")
		have = {r.role for r in rp.roles}
		missing = [r for r in GROUP_ADMIN_ROLES if r not in have and frappe.db.exists("Role", r)]
		for role in missing:
			rp.append("roles", {"role": role})
		if missing:
			rp.save(ignore_permissions=True)
	# Sales Manager cannot create Customers on its own; Sales User can.
	add_roles("mabdullahazizawan@gmail.com", ["Sales User"])

	frappe.db.commit()
	frappe.clear_cache()
	print("DONE")
