import frappe

ABBR = {"Al Hamdan Enterprise": "AHE", "Infiqo": "INF", "Uroojj": "URJ"}

# Inferred from each person's role/designation -- these are the standard Department
# records already seeded by install_fixtures (Step 1). Reassign if the user's actual
# org chart differs; this is a reasonable default, not confirmed by the user.
DEPARTMENT_BY_EMPLOYEE_NAME = {
	"Yasir Khan": "Management",
	"Abdullah Aziz": "Management",
	"Aaliyan Irfan": "Operations",
	"Arif Ali": "Operations",
	"Usman": "Human Resources",
	"Ahmed": "Marketing",
}


def run():
	for emp in frappe.get_all("Employee", fields=["name", "employee_name", "company"]):
		dept_base = DEPARTMENT_BY_EMPLOYEE_NAME.get(emp.employee_name)
		if not dept_base:
			continue
		abbr = ABBR[emp.company]
		dept = f"{dept_base} - {abbr}"
		if not frappe.db.exists("Department", dept):
			print("skipped, department not found:", dept)
			continue
		frappe.db.set_value("Employee", emp.name, "department", dept)
		print("set department", emp.employee_name, "->", dept)
	frappe.db.commit()
	print("DONE")
