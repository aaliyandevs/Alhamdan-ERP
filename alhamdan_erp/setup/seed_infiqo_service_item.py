import frappe

# Infiqo has no fixed packages, but ERPNext cannot create a Quotation or Invoice without
# an item row. This single non-stock item stands in for "whatever was agreed with this
# client": change the description, qty and rate on each document.
ITEM_CODE = "INF-CUSTOM-SERVICE"


def run():
	if not frappe.db.exists("Item", ITEM_CODE):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": ITEM_CODE,
				"item_name": "Custom Service",
				"item_group": "Services",
				"stock_uom": "Nos",
				"is_stock_item": 0,
				"is_sales_item": 1,
				"is_purchase_item": 0,
				"description": "Custom-scoped engagement. Replace with the agreed scope on each document.",
				"item_defaults": [{"company": "Infiqo"}],
			}
		).insert(ignore_permissions=True)
		print("created item", ITEM_CODE)
	frappe.db.commit()
	print("DONE")
