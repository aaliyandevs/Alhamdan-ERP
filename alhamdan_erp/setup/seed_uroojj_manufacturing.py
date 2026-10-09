import frappe

OPERATIONS = ["Compounding", "Bottle Filling", "Capping & Labeling", "Packaging & QC"]
WORKSTATIONS = ["Compounding Station", "Filling Line", "Labeling Station", "Packaging Bench"]

QC_TEMPLATE = "Uroojj Finished Goods QC"
QC_PARAMETERS = ["Fragrance Match", "Fill Volume", "Bottle Seal / Leak Check", "Label Placement", "Box/Packaging Condition"]


def run():
	for op in OPERATIONS:
		if not frappe.db.exists("Operation", op):
			frappe.get_doc({"doctype": "Operation", "name": op}).insert(ignore_permissions=True)
			print("created operation", op)

	for ws in WORKSTATIONS:
		if not frappe.db.exists("Workstation", ws):
			w = frappe.new_doc("Workstation")
			w.workstation_name = ws
			w.flags.ignore_mandatory = True
			w.insert(ignore_permissions=True)
			print("created workstation", ws)

	for p in QC_PARAMETERS:
		if not frappe.db.exists("Quality Inspection Parameter", p):
			frappe.get_doc({"doctype": "Quality Inspection Parameter", "parameter": p}).insert(ignore_permissions=True)
			print("created QC parameter", p)

	if not frappe.db.exists("Quality Inspection Template", QC_TEMPLATE):
		qt = frappe.new_doc("Quality Inspection Template")
		qt.quality_inspection_template_name = QC_TEMPLATE
		for p in QC_PARAMETERS:
			qt.append("item_quality_inspection_parameter", {"specification": p, "numeric": 0})
		qt.insert(ignore_permissions=True)
		print("created QC template", QC_TEMPLATE)

	frappe.db.commit()
	print("DONE")
