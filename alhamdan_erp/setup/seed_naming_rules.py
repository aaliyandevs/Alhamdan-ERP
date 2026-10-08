import frappe

# Company-prefixed document numbering so Infiqo vs Uroojj transactions are
# distinguishable at a glance (e.g. INF-SINV-2026-00001 vs URJ-SINV-2026-00001).
# Uses core Frappe's Document Naming Rule (condition-based), not a Property
# Setter hack on naming_series options -- safer, reversible, no risk to the
# existing default naming series (still there as a fallback if these are disabled).

ABBR = {"Al Hamdan Enterprise": "AHE", "Infiqo": "INF", "Uroojj": "URJ"}

RULES = [
	("Sales Invoice", "SINV"),
	("Quotation", "QTN"),
	("Sales Order", "SO"),
	("Delivery Note", "DN"),
	("Purchase Invoice", "PINV"),
	("Purchase Order", "PO"),
]


def run():
	for doctype, code in RULES:
		for company, abbr in ABBR.items():
			rule_name = f"{abbr}-{code}"
			if frappe.db.exists("Document Naming Rule", rule_name):
				continue
			doc = frappe.new_doc("Document Naming Rule")
			doc.document_type = doctype
			doc.priority = 1
			doc.prefix = f"{abbr}-{code}-.YYYY.-"
			doc.prefix_digits = 5
			doc.append("conditions", {"field": "company", "condition": "=", "value": company})
			try:
				doc.insert(ignore_permissions=True)
			except Exception as e:
				print("SKIPPED", doctype, company, "->", e)
				continue
			if doc.name != rule_name:
				frappe.rename_doc("Document Naming Rule", doc.name, rule_name, force=True)
			print("created naming rule", rule_name, "for", doctype)
	frappe.db.commit()
	print("DONE")
