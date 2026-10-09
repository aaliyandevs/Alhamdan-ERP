import json

import frappe

# Home shows exactly three tiles: the group (combined view of all companies) and the two
# operating companies. Each opens its own sidebar + landing page, pre-filtered to that company.
# Re-applied after every migrate (see hooks.py) because Frappe re-syncs its standard tiles.

GROUP = "Al Hamdan Enterprise"


def dt(label, doctype=None, company=True):
	return {"kind": "doctype", "label": label, "target": doctype or label, "company": company}


def rpt(label, report=None, company=True):
	return {"kind": "report", "label": label, "target": report or label, "company": company}


def url(label, path):
	return {"kind": "url", "label": label, "target": path}


def sec(label):
	return {"kind": "section", "label": label}


def spec_for(company):
	if company == "Infiqo":
		return [
			sec("Sales"),
			dt("Quotation"), dt("Sales Order"), dt("Sales Invoice"), dt("Payment Entry"), dt("Customer", company=False),
			url("Infiqo CRM (leads & deals)", "/crm"),
			sec("Delivery"),
			dt("Project"), dt("Task"), dt("Timesheet"), dt("Project Template", company=False),
			sec("Support"),
			url("Support Desk (tickets)", "/helpdesk"),
			sec("People"),
			dt("Employee"), dt("Leave Application"), dt("Attendance"), dt("Salary Slip"),
			sec("Accounts"),
			dt("Journal Entry"), rpt("General Ledger"), rpt("Accounts Receivable"), rpt("Profit and Loss Statement"), rpt("Trial Balance"),
		]
	if company == "Uroojj":
		return [
			sec("Sales"),
			dt("Sales Order"), dt("Sales Invoice"), dt("Delivery Note"), dt("Payment Entry"), dt("Customer", company=False),
			sec("Purchasing"),
			dt("Supplier", company=False), dt("Purchase Order"), dt("Purchase Receipt"), dt("Purchase Invoice"),
			sec("Inventory"),
			dt("Item", company=False), dt("Stock Entry"), dt("Warehouse"), rpt("Stock Balance"), rpt("Stock Ledger"),
			sec("Production & Quality"),
			dt("BOM"), dt("Work Order"), dt("Quality Inspection"),
			sec("Support"),
			url("Support Desk (customer service)", "/helpdesk"),
			sec("People"),
			dt("Employee"), dt("Leave Application"), dt("Salary Slip"),
			sec("Accounts"),
			dt("Journal Entry"), rpt("General Ledger"), rpt("Accounts Receivable"), rpt("Accounts Payable"), rpt("Profit and Loss Statement"), rpt("Trial Balance"),
		]
	# Group: combined view, no company filter
	return [
		sec("Group Finance (all companies)"),
		dt("Company", company=False), dt("Account", "Account", company=False), dt("Journal Entry", company=False),
		rpt("General Ledger", company=False), rpt("Trial Balance", company=False), rpt("Profit and Loss Statement", company=False),
		rpt("Balance Sheet", company=False), rpt("Accounts Receivable", company=False), rpt("Accounts Payable", company=False),
		dt("Payment Entry", company=False),
		sec("Sales & Purchasing (all companies)"),
		dt("Sales Invoice", company=False), dt("Sales Order", company=False), dt("Quotation", company=False),
		dt("Purchase Invoice", company=False), dt("Purchase Order", company=False),
		sec("Stock (all companies)"),
		dt("Item", company=False), dt("Stock Entry", company=False), rpt("Stock Balance", company=False),
		sec("People (all companies)"),
		dt("Employee", company=False), dt("Leave Application", company=False), dt("Salary Slip", company=False),
		dt("Payroll Entry", company=False), dt("Holiday List", company=False), dt("Leave Allocation", company=False),
		sec("Apps"),
		url("Infiqo CRM", "/crm"), url("Support Desk", "/helpdesk"),
		sec("Administration"),
		dt("User", company=False), dt("Role Profile", company=False), dt("User Permission", company=False),
		dt("Document Naming Rule", company=False), dt("System Settings", company=False),
		dt("Shopify Setting", company=False),
	]


def route(item, company):
	"""Return (link_type, link_to, url, filters_json) or None if the target does not exist."""
	kind, target = item["kind"], item["target"]
	flt = {"company": company} if item.get("company") and company != GROUP else {}
	if kind == "url":
		return "URL", None, target, None
	if kind == "doctype":
		if not frappe.db.exists("DocType", target):
			return None
		if flt and not frappe.get_meta(target).has_field("company"):
			flt = {}
		return "DocType", target, None, json.dumps(flt) if flt else None
	if kind == "report":
		if not frappe.db.exists("Report", target):
			return None
		return "Report", target, None, json.dumps(flt) if flt else None
	return None


def build_sidebar(company, items):
	sb = frappe.get_doc({"doctype": "Workspace Sidebar", "title": company, "header_icon": "building", "app": "alhamdan_erp", "standard": 0})
	sb.append("items", {"label": "Home", "type": "Link", "link_type": "Workspace", "link_to": company, "icon": "home", "collapsible": 1})
	child = False
	skipped = []
	for it in items:
		if it["kind"] == "section":
			sb.append("items", {"label": it["label"], "type": "Section Break", "indent": 1, "collapsible": 1, "keep_closed": 1})
			child = True
			continue
		r = route(it, company)
		if not r:
			skipped.append(it["label"])
			continue
		link_type, link_to, u, flt = r
		row = {"label": it["label"], "type": "Link", "link_type": link_type, "child": 1 if child else 0, "collapsible": 1}
		if link_to:
			row["link_to"] = link_to
		if u:
			row["url"] = u
		if flt:
			# NOT `filters`: core Frappe's SidebarItem.get_path() expects that field as a
			# list of [doctype, field, op, value] tuples; a plain dict throws inside
			# transform_filters() (Object.entries on undefined) and silently kills every
			# sidebar item rendered after it. `route_options` takes a plain dict safely.
			row["route_options"] = flt
		sb.append("items", row)
	sb.insert(ignore_permissions=True)
	return skipped


def build_workspace(company):
	# Landing page is intentionally empty (just the company name); every page and category lives in the
	# sidebar. Replace `content` here when the home page of each company is designed.
	ws = frappe.new_doc("Workspace")
	ws.title = company
	ws.label = company
	ws.public = 1
	ws.type = "Workspace"
	ws.app = "alhamdan_erp"
	ws.content = json.dumps([{"id": "hdr0000001", "type": "header", "data": {"text": f'<span class=\"h4\"><b>{company}</b></span>', "col": 12}}])
	ws.insert(ignore_permissions=True)



def apply():
	frappe.flags.in_patch = True
	order = [GROUP, "Infiqo", "Uroojj"]
	colors = {GROUP: "gray", "Infiqo": "blue", "Uroojj": "blue"}
	skipped_all = {}
	for company in order:
		items = spec_for(company)
		for dtype, name in (("Desktop Icon", company), ("Workspace Sidebar", company), ("Workspace", company)):
			if frappe.db.exists(dtype, name):
				frappe.delete_doc(dtype, name, ignore_permissions=True, force=True)
		build_workspace(company)
		skipped_all[company] = build_sidebar(company, items)
		frappe.get_doc(
			{
				"doctype": "Desktop Icon",
				"label": company,
				"icon_type": "Link",
				"link_type": "Workspace Sidebar",
				"link_to": company,
				"app": "alhamdan_erp",
				"standard": 0,
				"bg_color": colors[company],
				"idx": order.index(company),
				"hidden": 0,
			}
		).insert(ignore_permissions=True)

	# Everything else leaves the home screen. Children must be hidden too: a tile whose parent
	# folder is hidden is promoted to the top level.
	for name in frappe.get_all("Desktop Icon", filters={"name": ["not in", order]}, pluck="name"):
		frappe.db.set_value("Desktop Icon", name, "hidden", 1)
	frappe.db.commit()
	frappe.clear_cache()
	return skipped_all


def run():
	skipped = apply()
	print("skipped (target missing):", skipped)
	print("visible tiles:", frappe.get_all("Desktop Icon", filters={"hidden": 0}, pluck="label"))
	print("DONE")
