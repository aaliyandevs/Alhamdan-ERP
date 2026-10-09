import frappe

# Infiqo has no fixed item catalog -- every engagement is custom-scoped.
# These fields capture the agreed scope/package directly on the transaction
# instead of relying on a Price List / Item that doesn't exist.
CUSTOM_FIELDS = [
	("Quotation", "custom_service_scope", "Service Scope / Package", "Small Text", "Agreed scope of work for this custom engagement (Infiqo has no fixed item catalog)."),
	("Sales Order", "custom_service_scope", "Service Scope / Package", "Small Text", "Agreed scope of work, carried through to the invoice."),
	("Sales Invoice", "custom_service_scope", "Service Scope / Package", "Small Text", "Scope of work this invoice covers."),
	("Project", "custom_service_scope", "Service Scope / Package", "Small Text", "Agreed scope for this client engagement."),
]

PAYMENT_TERMS = [
	# name, invoice_portion, due_date_based_on, credit_days, description
	("Infiqo - 50% Advance", 50, "Day(s) after invoice date", 0, "50% due immediately on invoice."),
	("Infiqo - 50% on Delivery", 50, "Day(s) after invoice date", 30, "Remaining 50% due on project delivery/completion."),
	("Infiqo - Retainer Net 15", 100, "Day(s) after invoice date", 15, "Monthly retainer, due 15 days from invoice date."),
	("Uroojj - Cash on Delivery", 100, "Day(s) after invoice date", 0, "Full amount collected on delivery (COD)."),
]

TEMPLATES = [
	("Infiqo - Project (50/50)", ["Infiqo - 50% Advance", "Infiqo - 50% on Delivery"]),
	("Infiqo - Monthly Retainer", ["Infiqo - Retainer Net 15"]),
	("Uroojj - COD", ["Uroojj - Cash on Delivery"]),
]


def run():
	for dt, fieldname, label, fieldtype, desc in CUSTOM_FIELDS:
		if frappe.db.exists("Custom Field", f"{dt}-{fieldname}"):
			continue
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": dt,
				"fieldname": fieldname,
				"label": label,
				"fieldtype": fieldtype,
				"description": desc,
				"insert_after": "customer_name" if dt != "Project" else "project_name",
			}
		).insert(ignore_permissions=True)
		print("created custom field", dt, fieldname)

	for name, portion, due_based_on, credit_days, desc in PAYMENT_TERMS:
		if frappe.db.exists("Payment Term", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Payment Term",
				"payment_term_name": name,
				"invoice_portion": portion,
				"due_date_based_on": due_based_on,
				"credit_days": credit_days,
				"description": desc,
			}
		).insert(ignore_permissions=True)
		print("created payment term", name)

	for template_name, terms in TEMPLATES:
		if frappe.db.exists("Payment Terms Template", template_name):
			continue
		doc = frappe.get_doc({"doctype": "Payment Terms Template", "template_name": template_name})
		for t in terms:
			pt = frappe.get_doc("Payment Term", t)
			doc.append(
				"terms",
				{
					"payment_term": pt.name,
					"description": pt.description,
					"invoice_portion": pt.invoice_portion,
					"due_date_based_on": pt.due_date_based_on,
					"credit_days": pt.credit_days,
				},
			)
		doc.insert(ignore_permissions=True)
		print("created payment terms template", template_name)

	frappe.db.commit()
	print("DONE")
