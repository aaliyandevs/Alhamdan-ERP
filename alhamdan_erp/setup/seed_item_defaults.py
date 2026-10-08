import frappe

# Each Uroojj perfume is sold as a finished good, so default its stock to
# "Finished Goods - URJ" (also the natural target for Shopify stock sync).
COMPANY = "Uroojj"
WAREHOUSE = "Finished Goods - URJ"


def run():
	for code in frappe.get_all("Item", filters={"item_group": "Fragrances"}, pluck="name"):
		item = frappe.get_doc("Item", code)
		if any(d.company == COMPANY for d in item.item_defaults):
			continue
		item.append("item_defaults", {"company": COMPANY, "default_warehouse": WAREHOUSE})
		item.save(ignore_permissions=True)
		print("default warehouse set for", code)
	frappe.db.commit()
	print("DONE")
