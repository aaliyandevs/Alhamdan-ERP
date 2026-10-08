import frappe

ABBR = {"Al Hamdan Enterprise": "AHE", "Infiqo": "INF", "Uroojj": "URJ"}


def map_account(mode, company, account):
	doc = frappe.get_doc("Mode of Payment", mode)
	if any(r.company == company for r in doc.accounts):
		return
	doc.append("accounts", {"company": company, "default_account": account})
	doc.save(ignore_permissions=True)
	print("mapped", mode, company, "->", account)


def run():
	for company, abbr in ABBR.items():
		map_account("Cash", company, f"Cash - {abbr}")

	# Uroojj is 100% COD. Mapped to Cash for now; if courier remittances should
	# land in a bank or a "COD receivable from courier" account, change it here.
	if not frappe.db.exists("Mode of Payment", "Cash on Delivery"):
		frappe.get_doc({"doctype": "Mode of Payment", "mode_of_payment": "Cash on Delivery", "type": "Cash"}).insert(
			ignore_permissions=True
		)
		print("created Cash on Delivery")
	map_account("Cash on Delivery", "Uroojj", "Cash - URJ")

	frappe.db.commit()
	print("DONE")
