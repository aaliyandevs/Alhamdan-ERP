import frappe

ABBR = {"Al Hamdan Enterprise": "AHE", "Infiqo": "INF", "Uroojj": "URJ"}


def make_account(company, name, parent, account_type=None):
	abbr = ABBR[company]
	full = f"{name} - {abbr}"
	if frappe.db.exists("Account", full):
		return full
	parent_full = f"{parent} - {abbr}"
	if not frappe.db.exists("Account", parent_full):
		frappe.throw(f"Parent account missing: {parent_full}")
	doc = {
		"doctype": "Account",
		"account_name": name,
		"company": company,
		"parent_account": parent_full,
		"is_group": 0,
	}
	if account_type:
		doc["account_type"] = account_type
	frappe.get_doc(doc).insert(ignore_permissions=True)
	print("created account", full)
	return full


def make_template(company, title, taxes):
	abbr = ABBR[company]
	name = f"{title} - {abbr}"
	if frappe.db.exists("Sales Taxes and Charges Template", name):
		return
	frappe.get_doc(
		{
			"doctype": "Sales Taxes and Charges Template",
			"title": title,
			"company": company,
			"taxes": taxes,
		}
	).insert(ignore_permissions=True)
	print("created template", name)


def make_warehouse(company, name, parent="All Warehouses"):
	abbr = ABBR[company]
	full = f"{name} - {abbr}"
	if frappe.db.exists("Warehouse", full):
		return
	wh = frappe.get_doc(
		{
			"doctype": "Warehouse",
			"warehouse_name": name,
			"company": company,
			"parent_warehouse": f"{parent} - {abbr}",
			"is_group": 0,
		}
	)
	wh.flags.ignore_permissions = True
	wh.flags.ignore_mandatory = True
	wh.flags.ignore_inventory_account_validation = True
	wh.insert()
	print("created warehouse", full)


def make_price_list(name, currency):
	if frappe.db.exists("Price List", name):
		return
	frappe.db.set_value("Currency", currency, "enabled", 1)
	frappe.get_doc(
		{
			"doctype": "Price List",
			"price_list_name": name,
			"currency": currency,
			"selling": 1,
			"enabled": 1,
		}
	).insert(ignore_permissions=True)
	print("created price list", name)


def run():
	settings = frappe.get_single("Currency Exchange Settings")
	settings.service_provider = "frankfurter.dev - v2"
	settings.disabled = 0
	settings.save(ignore_permissions=True)
	print("exchange provider:", settings.service_provider)

	make_price_list("Standard Selling", "PKR")
	make_price_list("Standard Selling USD", "USD")

	for code, price in [
		("URJ-BERRY-AURA", 2699),
		("URJ-STORM-LEGEND", 2999),
		("URJ-CORPORATE-AUTHORITY", 3099),
		("URJ-BLACK-DOMINION", 3099),
		("URJ-VELVET-POUR", 3599),
	]:
		if not frappe.db.exists("Item Price", {"item_code": code, "price_list": "Standard Selling"}):
			frappe.get_doc(
				{
					"doctype": "Item Price",
					"item_code": code,
					"price_list": "Standard Selling",
					"price_list_rate": price,
					"currency": "PKR",
					"selling": 1,
				}
			).insert(ignore_permissions=True)
			print("item price", code, price)

	make_account("Al Hamdan Enterprise", "Sindh Sales Tax on Services (SRB)", "Duties and Taxes", "Tax")
	make_account("Al Hamdan Enterprise", "Export Proceeds Final Tax 0.25%", "Indirect Expenses")
	make_account("Al Hamdan Enterprise", "Sales Tax Payable (GST 18%)", "Duties and Taxes", "Tax")
	srb = "Sindh Sales Tax on Services (SRB) - INF"
	gst = "Sales Tax Payable (GST 18%) - URJ"
	for acct in (srb, gst, "Export Proceeds Final Tax 0.25% - INF"):
		if not frappe.db.exists("Account", acct):
			frappe.throw(f"Account did not sync to child company: {acct}")
	make_template(
		"Infiqo",
		"SRB Sindh Services Tax 15% (Standard)",
		[{"charge_type": "On Net Total", "account_head": srb, "description": "Sindh Sales Tax on Services 15%", "rate": 15}],
	)
	make_template(
		"Infiqo",
		"SRB Sindh Services Tax 3% (IT Reduced Rate)",
		[{"charge_type": "On Net Total", "account_head": srb, "description": "Sindh Sales Tax on Services 3% (IT reduced rate, no input credit)", "rate": 3}],
	)
	make_template("Infiqo", "Export Zero-Rated (International)", [])

	make_template(
		"Uroojj",
		"GST 18%",
		[{"charge_type": "On Net Total", "account_head": gst, "description": "GST 18%", "rate": 18}],
	)

	make_warehouse("Uroojj", "Raw Material")
	make_warehouse("Uroojj", "Dispatch")

	frappe.db.commit()
	print("DONE")
