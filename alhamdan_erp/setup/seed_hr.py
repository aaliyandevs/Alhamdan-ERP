import frappe
from frappe.utils import getdate

HOLIDAY_LIST = "Pakistan Holidays FY2026-27"
LEAVE_PERIOD = "FY 2026-2027"
LEAVE_POLICY = "2 Leaves Per Month"

GOV_HOLIDAYS = [
	("2026-08-14", "Independence Day"),
	("2026-08-25", "Eid Milad-un-Nabi"),
	("2026-11-09", "Allama Iqbal Day"),
	("2026-12-25", "Quaid-e-Azam Day"),
	("2027-02-05", "Kashmir Day"),
	("2027-03-10", "Eid ul Fitr"),
	("2027-03-11", "Eid ul Fitr"),
	("2027-03-12", "Eid ul Fitr"),
	("2027-03-23", "Pakistan Day"),
	("2027-05-01", "Labour Day"),
	("2027-05-17", "Eid ul Adha"),
	("2027-05-18", "Eid ul Adha"),
	("2027-05-19", "Eid ul Adha"),
]

EMPLOYEES = [
	("Syed Ameen Ul Hassan Hamdani", "syedameenulhassanhamdani786@gmail.com", "Founder", "Al Hamdan Enterprise"),
	("Yasir Khan", None, "COO", "Al Hamdan Enterprise"),
	("Abdullah Aziz", "mabdullahazizawan@gmail.com", "Manager", "Infiqo"),
	("Aaliyan Irfan", "aaliyan.devs@gmail.com", "Developer", "Infiqo"),
	("Arif Ali", "arifsabzali6@gmail.com", "Designer", "Infiqo"),
	("Usman", "usmanzubairkhan9@gmail.com", "HR Manager", "Infiqo"),
	("Ahmed", "mohammadahmedhanfi@gmail.com", "Marketer", "Infiqo"),
]


def run():
	if not frappe.db.exists("Holiday List", HOLIDAY_LIST):
		hl = frappe.new_doc("Holiday List")
		hl.holiday_list_name = HOLIDAY_LIST
		hl.from_date = "2026-07-01"
		hl.to_date = "2027-06-30"
		for day in ("Saturday", "Sunday"):
			hl.weekly_off = day
			hl.get_weekly_off_dates()
		for date, desc in GOV_HOLIDAYS:
			if getdate(date).weekday() >= 5:
				print("skipped (already weekend):", date, desc)
				continue
			hl.append("holidays", {"holiday_date": date, "description": desc})
		hl.insert(ignore_permissions=True)
		print("created holiday list", HOLIDAY_LIST, "total holidays:", hl.total_holidays)

	for company in ("Al Hamdan Enterprise", "Infiqo", "Uroojj"):
		frappe.db.set_value("Company", company, "default_holiday_list", HOLIDAY_LIST)

	for desig in {e[2] for e in EMPLOYEES}:
		if not frappe.db.exists("Designation", desig):
			frappe.get_doc({"doctype": "Designation", "designation_name": desig}).insert(ignore_permissions=True)
			print("created designation", desig)

	if not frappe.db.exists("Leave Type", "Casual Leave"):
		frappe.get_doc({"doctype": "Leave Type", "leave_type_name": "Casual Leave"}).insert(ignore_permissions=True)
	lt = frappe.get_doc("Leave Type", "Casual Leave")
	lt.is_earned_leave = 1
	lt.earned_leave_frequency = "Monthly"
	lt.max_leaves_allowed = 24
	lt.allow_negative = 0
	lt.is_carry_forward = 0
	lt.save(ignore_permissions=True)
	print("leave type configured: Casual Leave (earned monthly)")

	if not frappe.db.exists("Leave Period", LEAVE_PERIOD):
		frappe.get_doc(
			{
				"doctype": "Leave Period",
				"leave_period_name": LEAVE_PERIOD,
				"from_date": "2026-07-01",
				"to_date": "2027-06-30",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)
		print("created leave period")

	if not frappe.db.exists("Leave Policy", LEAVE_POLICY):
		lp = frappe.get_doc(
			{
				"doctype": "Leave Policy",
				"title": LEAVE_POLICY,
				"leave_policy_details": [{"leave_type": "Casual Leave", "annual_allocation": 24}],
			}
		)
		lp.insert(ignore_permissions=True)
		if lp.meta.is_submittable:
			lp.submit()
		print("created leave policy", lp.name)
	policy_name = frappe.db.get_value("Leave Policy", {"title": LEAVE_POLICY}, "name")

	for full_name, email, desig, company in EMPLOYEES:
		existing = frappe.db.get_value("Employee", {"employee_name": full_name}, "name")
		if existing:
			print("employee exists:", existing)
			continue
		emp = frappe.new_doc("Employee")
		emp.first_name = full_name
		emp.company = company
		emp.designation = desig
		emp.status = "Active"
		emp.holiday_list = HOLIDAY_LIST
		if email:
			emp.user_id = email
		emp.flags.ignore_mandatory = True
		emp.insert(ignore_permissions=True)
		print("created employee", emp.name, full_name, desig, company)

	frappe.db.commit()
	print("leave policy name:", policy_name)
	print("DONE")
