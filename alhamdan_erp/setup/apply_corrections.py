import frappe
from frappe.utils import getdate

JOIN_DATE = "2026-06-01"
LEAVE_POLICY = "HR-LPOL-2026-00001"
LEAVE_PERIOD = "HR-LPR-2026-00001"
HOLIDAY_LIST = "Pakistan Holidays FY2026-27"

ALL_COMPANY_USERS = [
	"mabdullahazizawan@gmail.com",
	"aaliyan.devs@gmail.com",
	"arifsabzali6@gmail.com",
	"usmanzubairkhan9@gmail.com",
	"mohammadahmedhanfi@gmail.com",
]


def run():
	for g in ("Male", "Female", "Other", "Prefer not to say"):
		if not frappe.db.exists("Gender", g):
			frappe.get_doc({"doctype": "Gender", "gender": g}).insert(ignore_permissions=True)
			print("created gender", g)

	# 1. Yasir Khan's user (same tier as the Founder: unrestricted group admin)
	email = "iamyasirmarwat@gmail.com"
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Yasir Khan",
				"send_welcome_email": 0,
				"enabled": 1,
				"user_type": "System User",
			}
		).insert(ignore_permissions=True)
		print("created user", email)
	user = frappe.get_doc("User", email)
	have = {r.role for r in user.roles}
	for role in ("System Manager", "Accounts Manager"):
		if role not in have:
			user.append("roles", {"role": role})
	user.save(ignore_permissions=True)

	# 2. Remove company restriction for the 5 users who work across all 3 brands
	for u in ALL_COMPANY_USERS:
		for name in frappe.get_all("User Permission", filters={"user": u, "allow": "Company"}, pluck="name"):
			frappe.delete_doc("User Permission", name, ignore_permissions=True)
			print("removed company restriction:", u)

	# 3. Delete the Founder's Employee record (he's the owner, not staff)
	founder_emp = frappe.db.get_value("Employee", {"employee_name": "Syed Ameen Ul Hassan Hamdani"}, "name")
	if founder_emp:
		frappe.delete_doc("Employee", founder_emp, ignore_permissions=True, force=True)
		print("deleted founder employee record", founder_emp)

	# 4. Yasir's employee record: link user, set gender/join date, no self-only restriction
	yasir_emp = frappe.db.get_value("Employee", {"employee_name": "Yasir Khan"}, "name")
	emp = frappe.get_doc("Employee", yasir_emp)
	emp.user_id = email
	emp.gender = "Male"
	emp.date_of_joining = JOIN_DATE
	emp.create_user_permission = 0
	emp.flags.ignore_mandatory = True
	emp.save(ignore_permissions=True)
	for name in frappe.get_all("User Permission", filters={"user": email, "allow": "Employee"}, pluck="name"):
		frappe.delete_doc("User Permission", name, ignore_permissions=True)

	# 5. Gender + joining date for all remaining employees
	for emp_name in frappe.get_all("Employee", pluck="name"):
		doc = frappe.get_doc("Employee", emp_name)
		doc.gender = "Male"
		doc.date_of_joining = JOIN_DATE
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)

	frappe.db.commit()

	# 6. Leave Policy Assignments for every remaining employee
	for emp_name in frappe.get_all("Employee", pluck="name"):
		if frappe.db.exists("Leave Policy Assignment", {"employee": emp_name}):
			continue
		lpa = frappe.new_doc("Leave Policy Assignment")
		lpa.employee = emp_name
		lpa.assignment_based_on = "Leave Period"
		lpa.leave_period = LEAVE_PERIOD
		lpa.leave_policy = LEAVE_POLICY
		lpa.effective_from = "2026-07-01"
		lpa.effective_to = "2027-06-30"
		lpa.insert(ignore_permissions=True)
		if lpa.meta.is_submittable:
			lpa.submit()
		print("leave policy assigned:", emp_name)

	frappe.db.commit()
	print("DONE")
