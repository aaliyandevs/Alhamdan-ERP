import frappe

# Pakistan's domestic e-commerce withholding tax (Finance Act 2026): 1% if paid
# digitally, 2% if COD. Uroojj is 100% COD, so only the 2% category is built.
# This is a regulatory rate, not a business judgment call -- unlike the Infiqo
# Sindh 15%/3% choice, which still needs the user's SRB filing decision.
CATEGORY = "Uroojj COD E-Commerce Withholding 2%"


def run():
	withholding_account = "TDS Payable - URJ"
	if not frappe.db.exists("Account", withholding_account):
		# Group-company rule: new accounts must be created at the root company
		# (Al Hamdan Enterprise); ERPNext syncs them down to Uroojj automatically.
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": "TDS Payable",
				"company": "Al Hamdan Enterprise",
				"parent_account": "Duties and Taxes - AHE",
				"account_type": "Tax",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
		if not frappe.db.exists("Account", withholding_account):
			frappe.throw(f"Account did not sync to Uroojj: {withholding_account}")
		print("created account", withholding_account)
	frappe.db.commit()

	if frappe.db.exists("Tax Withholding Category", CATEGORY):
		print("already exists:", CATEGORY)
		return

	cat = frappe.get_doc(
		{
			"doctype": "Tax Withholding Category",
			"name": CATEGORY,
			"category_name": CATEGORY,
			"tax_deduction_basis": "Net Total",
			"rates": [
				{
					"from_date": "2026-07-01",
					"to_date": "2030-06-30",
					"tax_withholding_rate": 2,
					"single_threshold": 0,
					"cumulative_threshold": 0,
				}
			],
			"accounts": [{"company": "Uroojj", "account": withholding_account}],
		}
	)
	cat.insert(ignore_permissions=True)
	frappe.db.commit()
	print("created", CATEGORY)
	print("DONE")
