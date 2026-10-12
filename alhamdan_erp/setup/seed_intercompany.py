import frappe

# Infiqo built Uroojj's website -- a real intercompany transaction (per the approved plan,
# "optionally tracking intercompany work... once basics are running"). This wires up the
# linkage ERPNext needs to post that as a proper Sales Invoice (Infiqo) <-> Purchase Invoice
# (Uroojj) pair via the "Inter Company Invoice" feature, with no amounts/dates assumed --
# those are a real transaction the user enters later once they decide what to bill.


def run():
	# Internal Customer "Uroojj" in Infiqo's books: lets Infiqo raise a Sales Invoice against Uroojj.
	if not frappe.db.exists("Customer", "Uroojj"):
		cust = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": "Uroojj",
			"customer_type": "Company",
			"customer_group": "Commercial",
			"territory": "Pakistan",
			"is_internal_customer": 1,
			"represents_company": "Uroojj",
			"companies": [{"company": "Infiqo"}],
		})
		cust.insert(ignore_permissions=True)
		print("created internal customer: Uroojj (represents_company=Uroojj, usable from Infiqo)")
	else:
		print("internal customer Uroojj already exists, skipped")

	# Internal Supplier "Infiqo" in Uroojj's books: lets Uroojj book the matching Purchase Invoice.
	if not frappe.db.exists("Supplier", "Infiqo"):
		supp = frappe.get_doc({
			"doctype": "Supplier",
			"supplier_name": "Infiqo",
			"supplier_group": "Services",
			"supplier_type": "Company",
			"is_internal_supplier": 1,
			"represents_company": "Infiqo",
			"companies": [{"company": "Uroojj"}],
		})
		supp.insert(ignore_permissions=True)
		print("created internal supplier: Infiqo (represents_company=Infiqo, usable from Uroojj)")
	else:
		print("internal supplier Infiqo already exists, skipped")

	frappe.db.commit()
	print("DONE")
