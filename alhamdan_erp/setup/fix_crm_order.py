import frappe

ORDER = {
	"Discovery": 1,
	"Strategy": 2,
	"Design & Build": 3,
	"Launch & Grow": 4,
	"Won": 5,
	"Lost": 6,
}

# Frappe CRM's built-in stages, replaced by Infiqo's own 4-stage process.
UNUSED_DEFAULTS = ["Qualification", "Demo/Making", "Proposal/Quotation", "Negotiation", "Ready to Close"]


def run():
	for name, position in ORDER.items():
		if frappe.db.exists("CRM Deal Status", name):
			frappe.db.set_value("CRM Deal Status", name, "position", position)

	for name in UNUSED_DEFAULTS:
		if not frappe.db.exists("CRM Deal Status", name):
			continue
		in_use = frappe.db.count("CRM Deal", {"status": name})
		if in_use:
			print("kept", name, "- used by", in_use, "deal(s)")
			continue
		frappe.delete_doc("CRM Deal Status", name, ignore_permissions=True)
		print("deleted", name)

	frappe.db.commit()
	print(frappe.get_all("CRM Deal Status", fields=["name", "position"], order_by="position asc"))
