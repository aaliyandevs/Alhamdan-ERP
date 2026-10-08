import frappe

# Text-only placeholders (no logo/address supplied yet) just so Print Formats
# have something besides blank space, and so the mechanism/link is wired up.
# Replace `content` with real branded HTML once the user provides logo/address.
COMPANIES = ["Al Hamdan Enterprise", "Infiqo", "Uroojj"]


def run():
	for company in COMPANIES:
		lh_name = f"{company} (placeholder)"
		if not frappe.db.exists("Letter Head", lh_name):
			lh = frappe.get_doc(
				{
					"doctype": "Letter Head",
					"letter_head_name": lh_name,
					"source": "HTML",
					"content": f"<div style='text-align:center'><h2>{company}</h2></div>",
					"is_default": 0,
				}
			)
			lh.insert(ignore_permissions=True)
			print("created letter head", lh_name)
		frappe.db.set_value("Company", company, "default_letter_head", lh_name)
		print("linked default letterhead for", company)
	frappe.db.commit()
	print("DONE")
