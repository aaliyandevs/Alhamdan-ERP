import frappe

# Infiqo's own 4-stage process (from the approved plan): Discovery -> Strategy -> Design & Build -> Launch & Grow
DEAL_STAGES = [
	("Discovery", 10, "Open", 10),
	("Strategy", 30, "Ongoing", 25),
	("Design & Build", 60, "Ongoing", 50),
	("Launch & Grow", 90, "Ongoing", 75),
	("Won", 100, "Won", 100),
	("Lost", 110, "Lost", 0),
]

LEAD_STAGES = [
	("New", 10, "Open"),
	("Contacted", 20, "Open"),
	("Qualified", 30, "Ongoing"),
	("Nurture", 40, "Ongoing"),
	("Converted", 50, "Won"),
	("Disqualified", 60, "Lost"),
]

PROJECT_TEMPLATE = "Infiqo Client Delivery"
PROJECT_TASKS = ["Discovery", "Strategy", "Design & Build", "Launch & Grow"]


def run():
	for status, position, type_, probability in DEAL_STAGES:
		if frappe.db.exists("CRM Deal Status", status):
			continue
		frappe.get_doc(
			{
				"doctype": "CRM Deal Status",
				"deal_status": status,
				"position": position,
				"type": type_,
				"probability": probability,
			}
		).insert(ignore_permissions=True)
		print("created deal status", status)

	for status, position, type_ in LEAD_STAGES:
		if frappe.db.exists("CRM Lead Status", status):
			continue
		frappe.get_doc(
			{"doctype": "CRM Lead Status", "lead_status": status, "position": position, "type": type_}
		).insert(ignore_permissions=True)
		print("created lead status", status)

	if not frappe.db.exists("Project Template", PROJECT_TEMPLATE):
		task_names = []
		for subject in PROJECT_TASKS:
			existing = frappe.db.get_value("Task", {"subject": subject, "project": ("is", "not set")}, "name")
			if existing:
				task_names.append(existing)
				continue
			t = frappe.new_doc("Task")
			t.subject = subject
			t.status = "Open"
			t.flags.ignore_mandatory = True
			t.insert(ignore_permissions=True)
			task_names.append(t.name)
			print("created standalone task", t.name, subject)

		pt = frappe.new_doc("Project Template")
		pt.name = PROJECT_TEMPLATE
		for task_name, subject in zip(task_names, PROJECT_TASKS):
			pt.append("tasks", {"task": task_name, "subject": subject})
		pt.flags.ignore_mandatory = True
		pt.insert(ignore_permissions=True)
		print("created project template", PROJECT_TEMPLATE)

	frappe.db.commit()
	print("DONE")
