import frappe

# User already confirmed: office days Monday-Friday. Weekly off (Sat/Sun) comes from the
# Holiday List, not a field on Shift Type itself. Hours are a placeholder (9-6) -- adjust
# if the real office hours differ.
SHIFT_NAME = "General Shift"
HOLIDAY_LIST = "Pakistan Holidays FY2026-27"


def run():
	if not frappe.db.exists("Shift Type", SHIFT_NAME):
		frappe.get_doc(
			{
				"doctype": "Shift Type",
				"name": SHIFT_NAME,
				"start_time": "09:00:00",
				"end_time": "18:00:00",
				"holiday_list": HOLIDAY_LIST,
			}
		).insert(ignore_permissions=True)
		print("created shift type", SHIFT_NAME)

	for emp in frappe.get_all("Employee", pluck="name"):
		if frappe.db.exists("Shift Assignment", {"employee": emp, "shift_type": SHIFT_NAME, "status": "Active"}):
			continue
		company = frappe.db.get_value("Employee", emp, "company")
		sa = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"employee": emp,
				"shift_type": SHIFT_NAME,
				"company": company,
				"start_date": "2026-07-01",
				"status": "Active",
			}
		)
		sa.insert(ignore_permissions=True)
		if sa.meta.is_submittable:
			sa.submit()
		print("assigned shift to", emp)

	frappe.db.commit()
	print("DONE")
