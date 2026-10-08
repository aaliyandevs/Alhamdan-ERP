import frappe


def run():
	s = frappe.get_single("Accounts Settings")
	before = s.allow_multi_currency_invoices_against_single_party_account
	s.allow_multi_currency_invoices_against_single_party_account = 1
	s.save(ignore_permissions=True)
	frappe.db.commit()
	print("multi-currency-per-party before:", before, "after:", s.allow_multi_currency_invoices_against_single_party_account)
	print("DONE")
