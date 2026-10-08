import frappe

COMPANIES = [
	# name, abbr, parent, is_group
	("Al Hamdan Enterprise", "AHE", None, 1),
	("Infiqo", "INF", "Al Hamdan Enterprise", 0),
	("Uroojj", "URJ", "Al Hamdan Enterprise", 0),
]

FISCAL_YEARS = [
	("2025-2026", "2025-07-01", "2026-06-30"),
	("2026-2027", "2026-07-01", "2027-06-30"),
]


def run():
	# This site is provisioned without ERPNext's setup wizard, so the things the
	# wizard normally seeds have to be created here, in this order.
	from erpnext.setup.setup_wizard.operations.install_fixtures import install

	install(country="Pakistan")
	frappe.db.commit()

	for gender in ("Male", "Female", "Other", "Prefer not to say"):
		if not frappe.db.exists("Gender", gender):
			frappe.get_doc({"doctype": "Gender", "gender": gender}).insert(ignore_permissions=True)

	# Must exist before any Company is created, otherwise Company.on_update()
	# aborts on the "Goods In Transit" warehouse and skips cost centers/departments.
	if not frappe.db.exists("Warehouse Type", "Transit"):
		frappe.get_doc({"doctype": "Warehouse Type", "name": "Transit"}).insert(ignore_permissions=True)
	frappe.db.commit()

	for name, abbr, parent, is_group in COMPANIES:
		if frappe.db.exists("Company", name):
			continue
		doc = frappe.new_doc("Company")
		doc.company_name = name
		doc.abbr = abbr
		doc.default_currency = "PKR"
		doc.country = "Pakistan"
		if parent:
			doc.parent_company = parent
		doc.is_group = is_group
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		print("created company", name)

	for year, start, end in FISCAL_YEARS:
		if frappe.db.exists("Fiscal Year", year):
			continue
		try:
			frappe.get_doc(
				{"doctype": "Fiscal Year", "year": year, "year_start_date": start, "year_end_date": end}
			).insert(ignore_permissions=True)
		except Exception as e:
			# Known core bug: the "Notification for new fiscal year" alert throws after the row is saved.
			print("fiscal year insert raised (checking it saved):", type(e).__name__)
		frappe.db.commit()
		if not frappe.db.exists("Fiscal Year", year):
			frappe.throw(f"Fiscal Year {year} was not created")
		print("fiscal year", year, "ok")

	ss = frappe.get_single("System Settings")
	ss.language = ss.language or "en"
	ss.time_zone = ss.time_zone or "Asia/Karachi"
	ss.country = ss.country or "Pakistan"
	ss.setup_complete = 1
	ss.save(ignore_permissions=True)

	# frappe.is_setup_complete() reads these rows, not System Settings.
	for app in ("frappe", "erpnext"):
		for row in frappe.get_all("Installed Application", filters={"app_name": app}, pluck="name"):
			frappe.db.set_value("Installed Application", row, "is_setup_complete", 1)

	gd = frappe.get_single("Global Defaults")
	gd.default_company = "Al Hamdan Enterprise"
	gd.save(ignore_permissions=True)

	frappe.db.commit()
	frappe.clear_cache()
	print("DONE")
