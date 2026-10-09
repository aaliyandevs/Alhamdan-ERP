import frappe
from frappe.utils import add_days, getdate, now_datetime, nowdate

OUT = []
C = {}


def step(label, fn):
	try:
		r = fn()
		OUT.append(f"PASS  {label}" + (f"  -> {r}" if r is not None else ""))
		return True
	except Exception as e:
		OUT.append(f"FAIL  {label}: {type(e).__name__}: {str(e)[:260]}")
		return False


def expect_fail(label, fn):
	try:
		fn()
		OUT.append(f"FAIL  {label}: expected ERPNext to reject this, but it was accepted")
	except Exception as e:
		OUT.append(f"PASS  {label} (correctly rejected)  -> {type(e).__name__}: {str(e)[:110]}")


def section(name, fn):
	OUT.append(f"\n## {name}")
	frappe.db.savepoint("sec")
	try:
		fn()
	except Exception as e:
		OUT.append(f"SECTION ERROR {name}: {type(e).__name__}: {str(e)[:260]}")
	finally:
		frappe.db.rollback(save_point="sec")


def gl(voucher_type, name):
	rows = frappe.get_all("GL Entry", filters={"voucher_type": voucher_type, "voucher_no": name, "is_cancelled": 0}, fields=["account", "debit", "credit"])
	return rows, round(sum(r.debit for r in rows) - sum(r.credit for r in rows), 2)


def submit(doc):
	doc.insert(ignore_permissions=True)
	doc.submit()
	return doc


# ---------------------------------------------------------------- Uroojj
def uroojj():
	from erpnext.stock.utils import get_stock_balance

	grp = frappe.db.get_value("Supplier Group", {"is_group": 0}, "name")
	frappe.get_doc({"doctype": "Supplier", "supplier_name": "TMP Supplier", "supplier_group": grp}).insert(ignore_permissions=True)
	frappe.get_doc({"doctype": "Item", "item_code": "TMP-RM1", "item_name": "TMP RM", "item_group": "Raw Material", "stock_uom": "Nos", "is_stock_item": 1}).insert(ignore_permissions=True)

	def purchase_receipt():
		pr = frappe.new_doc("Purchase Receipt")
		pr.company = "Uroojj"
		pr.supplier = "TMP Supplier"
		pr.append("items", {"item_code": "TMP-RM1", "qty": 100, "rate": 10, "warehouse": "Raw Material - URJ"})
		pr.set_missing_values()
		submit(pr)
		C["pr"] = pr.name
		return f"{pr.name} RM stock={get_stock_balance('TMP-RM1', 'Raw Material - URJ')}"

	step("Buy raw material (Purchase Receipt into Raw Material warehouse)", purchase_receipt)

	def purchase_invoice():
		from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

		pi = make_purchase_invoice(C["pr"])
		pi.bill_no = "TMP-1"
		submit(pi)
		assert pi.name.startswith("URJ-PINV-"), pi.name
		return f"{pi.name} total={pi.grand_total}"

	step("Purchase Invoice from receipt (+ URJ-PINV numbering)", purchase_invoice)

	def bom():
		b = frappe.new_doc("BOM")
		b.item = "URJ-BERRY-AURA"
		b.quantity = 1
		b.company = "Uroojj"
		b.currency = "PKR"
		b.append("items", {"item_code": "TMP-RM1", "qty": 2, "uom": "Nos", "stock_uom": "Nos", "conversion_factor": 1, "rate": 10})
		submit(b)
		C["bom"] = b.name
		assert round(b.total_cost, 2) == 20, b.total_cost
		return f"{b.name} cost={b.total_cost} (2 x 10)"

	step("Create + submit BOM for Berry Aura", bom)

	def work_order():
		from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

		wo = frappe.new_doc("Work Order")
		wo.production_item = "URJ-BERRY-AURA"
		wo.bom_no = C["bom"]
		wo.qty = 5
		wo.company = "Uroojj"
		wo.skip_transfer = 1
		wo.use_multi_level_bom = 0
		wo.source_warehouse = "Raw Material - URJ"
		wo.wip_warehouse = "Work In Progress - URJ"
		wo.fg_warehouse = "Finished Goods - URJ"
		wo.planned_start_date = nowdate()
		submit(wo)
		se = frappe.get_doc(make_stock_entry(wo.name, "Manufacture", 5))
		submit(se)
		fg = get_stock_balance("URJ-BERRY-AURA", "Finished Goods - URJ")
		rm = get_stock_balance("TMP-RM1", "Raw Material - URJ")
		assert fg == 5 and rm == 90, (fg, rm)
		C["mfg_se"] = se.name
		return f"{wo.name}: finished goods={fg}, raw material left={rm} (100-10)"

	step("Work Order -> Manufacture (raw material consumed, finished goods produced)", work_order)

	def qi():
		q = frappe.new_doc("Quality Inspection")
		q.inspection_type = "Outgoing"
		q.reference_type = "Stock Entry"
		q.reference_name = C["mfg_se"]
		q.item_code = "URJ-BERRY-AURA"
		q.sample_size = 1
		q.inspected_by = "Administrator"
		q.report_date = nowdate()
		q.quality_inspection_template = "Uroojj Finished Goods QC"
		q.get_item_specification_details()
		for r in q.readings:
			r.status = "Accepted"
			r.reading_1 = "OK"
		submit(q)
		return f"{q.name}: {len(q.readings)} QC parameters from template, status={q.status}"

	step("Quality Inspection using Uroojj QC template", qi)

	def delivery():
		dn = frappe.new_doc("Delivery Note")
		dn.company = "Uroojj"
		dn.customer = "Nooria Travels"
		dn.taxes_and_charges = "GST 18% - URJ"
		dn.append("items", {"item_code": "URJ-BERRY-AURA", "qty": 2, "rate": 2699, "warehouse": "Finished Goods - URJ"})
		dn.set_missing_values()
		submit(dn)
		assert dn.name.startswith("URJ-DN-"), dn.name
		left = get_stock_balance("URJ-BERRY-AURA", "Finished Goods - URJ")
		assert left == 3, left
		rows, diff = gl("Delivery Note", dn.name)
		C["dn"] = dn.name
		return f"{dn.name} stock left={left}, GL rows={len(rows)} (COGS/stock), debit-credit={diff}"

	step("Delivery Note (stock leaves, COGS posted, URJ-DN numbering)", delivery)

	def invoice():
		from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

		si = make_sales_invoice(C["dn"])
		si.payment_terms_template = "Uroojj - COD"
		submit(si)
		assert round(si.grand_total, 2) == 6369.64, si.grand_total
		rows, diff = gl("Sales Invoice", si.name)
		gst = sum(r.credit for r in rows if r.account == "Sales Tax Payable (GST 18%) - URJ")
		assert round(gst, 2) == 971.64 and diff == 0, (gst, diff)
		C["si"] = si.name
		return f"{si.name} total={si.grand_total}, GST credited={gst}, books balance (diff={diff})"

	step("Sales Invoice from Delivery Note (18% GST posts to GST account, books balance)", invoice)

	def payment():
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		pe = get_payment_entry("Sales Invoice", C["si"])
		pe.mode_of_payment = "Cash on Delivery"
		pe.paid_to = "Cash - URJ"
		pe.reference_no = "COD-1"
		pe.reference_date = nowdate()
		submit(pe)
		status, out = frappe.db.get_value("Sales Invoice", C["si"], ["status", "outstanding_amount"])
		assert status == "Paid" and out == 0, (status, out)
		return f"{pe.name}: invoice status={status}, outstanding={out}"

	step("COD payment settles the invoice", payment)

	def pdf():
		data = frappe.get_print("Sales Invoice", C["si"], as_pdf=True)
		assert data[:4] == b"%PDF", data[:20]
		return f"PDF generated, {len(data)} bytes"

	step("Sales Invoice prints to PDF (letterhead + wkhtmltopdf)", pdf)

	def oversell():
		dn = frappe.new_doc("Delivery Note")
		dn.company = "Uroojj"
		dn.customer = "Nooria Travels"
		dn.append("items", {"item_code": "URJ-BERRY-AURA", "qty": 100, "rate": 2699, "warehouse": "Finished Goods - URJ"})
		dn.set_missing_values()
		submit(dn)

	expect_fail("Cannot deliver more stock than exists", oversell)


# ---------------------------------------------------------------- Infiqo
def infiqo():
	def sales_chain():
		from erpnext.selling.doctype.quotation.quotation import make_sales_invoice, make_sales_order  # noqa
		from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice as so_to_si

		q = frappe.new_doc("Quotation")
		q.company = "Infiqo"
		q.quotation_to = "Customer"
		q.party_name = "Nooria Travels"
		q.currency = "USD"
		q.conversion_rate = 277
		q.selling_price_list = "Standard Selling USD"
		q.price_list_currency = "USD"
		q.plc_conversion_rate = 277
		q.payment_terms_template = "Infiqo - Project (50/50)"
		q.taxes_and_charges = "Export Zero-Rated (International) - INF"
		q.custom_service_scope = "Website redesign, 4 pages"
		q.append("items", {"item_code": "INF-CUSTOM-SERVICE", "qty": 1, "rate": 1200, "description": "Website redesign, 4 pages"})
		q.set_missing_values()
		submit(q)
		so = make_sales_order(q.name)
		so.delivery_date = add_days(nowdate(), 30)
		submit(so)
		si = so_to_si(so.name)
		submit(si)
		assert q.name.startswith("INF-QTN-") and so.name.startswith("INF-SO-") and si.name.startswith("INF-SINV-"), (q.name, so.name, si.name)
		C["usd_si"] = si.name
		return f"{q.name} -> {so.name} -> {si.name}, {si.grand_total} USD = {si.base_grand_total} PKR, scope kept={si.custom_service_scope!r}"

	step("Quotation -> Sales Order -> Sales Invoice in USD (Infiqo numbering, scope carried)", sales_chain)

	def usd_payment():
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		pe = get_payment_entry("Sales Invoice", C["usd_si"], party_amount=166200)
		pe.mode_of_payment = "Cash"
		pe.paid_to = "Cash - INF"
		pe.reference_no = "T1"
		pe.reference_date = nowdate()
		submit(pe)
		out = frappe.db.get_value("Sales Invoice", C["usd_si"], "outstanding_amount")
		return f"{pe.name}: received {pe.received_amount} PKR for {pe.paid_amount} USD, invoice outstanding now {out} USD"

	step("Receive first 50% (USD 600 = PKR 166,200) against the USD invoice", usd_payment)

	def sindh():
		si = frappe.new_doc("Sales Invoice")
		si.company = "Infiqo"
		si.customer = "Nooria Travels"
		si.selling_price_list = "Standard Selling"
		si.taxes_and_charges = "SRB Sindh Services Tax 3% (IT Reduced Rate) - INF"
		si.payment_terms_template = "Infiqo - Monthly Retainer"
		si.append("items", {"item_code": "INF-CUSTOM-SERVICE", "qty": 1, "rate": 100000})
		si.set_missing_values()
		submit(si)
		rows, diff = gl("Sales Invoice", si.name)
		srb = sum(r.credit for r in rows if r.account == "Sindh Sales Tax on Services (SRB) - INF")
		assert srb == 3000 and diff == 0, (srb, diff)
		return f"{si.name}: total={si.grand_total}, SRB tax credited={srb}, books balance"

	step("PKR invoice with Sindh 3% posts to SRB tax account", sindh)

	def project():
		frappe.get_doc({"doctype": "Activity Type", "activity_type": "TMP Dev"}).insert(ignore_permissions=True)
		p = frappe.new_doc("Project")
		p.project_name = "TMP Project"
		p.company = "Infiqo"
		p.customer = "Nooria Travels"
		p.project_template = "Infiqo Client Delivery"
		p.custom_service_scope = "Website redesign"
		p.insert(ignore_permissions=True)
		tasks = frappe.get_all("Task", filters={"project": p.name}, pluck="subject")
		assert sorted(tasks) == sorted(["Discovery", "Strategy", "Design & Build", "Launch & Grow"]), tasks
		C["proj"] = p.name
		C["task"] = frappe.db.get_value("Task", {"project": p.name, "subject": "Discovery"}, "name")
		return f"{p.name} auto-created tasks: {tasks}"

	step("Project from 'Infiqo Client Delivery' template creates the 4 stage tasks", project)

	def timesheet():
		ts = frappe.new_doc("Timesheet")
		ts.employee = "HR-EMP-00004"
		ts.company = "Infiqo"
		ts.append("time_logs", {"activity_type": "TMP Dev", "from_time": now_datetime(), "hours": 2, "project": C["proj"], "task": C["task"]})
		submit(ts)
		return f"{ts.name}: {ts.total_hours}h logged for Aaliyan on the project task"

	step("Developer logs a timesheet against the project task", timesheet)

	def crm():
		from crm.fcrm.doctype.crm_lead.crm_lead import convert_to_deal

		lead = frappe.get_doc({"doctype": "CRM Lead", "first_name": "TMP", "last_name": "Lead", "email": "tmp.lead@example.com", "organization": "TMP Org"}).insert(ignore_permissions=True)
		deal_name = convert_to_deal(lead=lead.name)
		deal = frappe.get_doc("CRM Deal", deal_name)
		start = deal.status
		path = [start]
		for st in ("Strategy", "Design & Build", "Launch & Grow", "Won"):
			deal.status = st
			deal.save(ignore_permissions=True)
			path.append(deal.status)
		return f"Lead -> Deal {deal.name}, stages walked: {' > '.join(path)}"

	step("CRM: Lead converts to Deal and moves through the Infiqo pipeline to Won", crm)

	def ticket():
		t = frappe.get_doc({"doctype": "HD Ticket", "subject": "TMP ticket", "raised_by": "client@example.com", "description": "test", "agent_group": "Infiqo Support"}).insert(ignore_permissions=True)
		return f"{t.name}: status={t.status}, team={t.agent_group}"

	step("Helpdesk: ticket raised and routed to Infiqo Support", ticket)


# ---------------------------------------------------------------- HR
def hr():
	from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on

	emp = "HR-EMP-00004"
	before = get_leave_balance_on(emp, "Casual Leave", "2026-10-30")

	def leave():
		la = frappe.new_doc("Leave Application")
		la.employee = emp
		la.leave_type = "Casual Leave"
		la.from_date = "2026-10-12"
		la.to_date = "2026-10-13"
		la.posting_date = nowdate()
		la.status = "Approved"
		submit(la)
		after = get_leave_balance_on(emp, "Casual Leave", "2026-10-30")
		assert after == before - 2, (before, after)
		return f"{la.name}: {la.total_leave_days} days, balance {before} -> {after}"

	step("Leave Application deducts from Casual Leave balance", leave)

	def too_much():
		la = frappe.new_doc("Leave Application")
		la.employee = emp
		la.leave_type = "Casual Leave"
		la.from_date = "2026-11-02"
		la.to_date = "2026-11-27"
		la.posting_date = nowdate()
		la.status = "Approved"
		submit(la)

	expect_fail("Cannot take more leave than the balance allows", too_much)

	def attendance():
		a = frappe.new_doc("Attendance")
		a.employee = emp
		a.status = "Present"
		a.attendance_date = "2026-10-08"
		a.company = "Infiqo"
		submit(a)
		return a.name

	step("Mark attendance", attendance)

	def payroll():
		from hrms.payroll.doctype.salary_structure.salary_structure import make_salary_slip

		frappe.get_doc({"doctype": "Salary Component", "salary_component": "TMP Basic", "salary_component_abbr": "TBS", "type": "Earning"}).insert(ignore_permissions=True)
		ss = frappe.new_doc("Salary Structure")
		ss.name = "TMP Structure"
		ss.company = "Infiqo"
		ss.payroll_frequency = "Monthly"
		ss.is_active = "Yes"
		ss.currency = "PKR"
		ss.append("earnings", {"salary_component": "TMP Basic", "abbr": "TBS", "amount": 100000})
		submit(ss)
		a = frappe.new_doc("Salary Structure Assignment")
		a.employee = emp
		a.salary_structure = ss.name
		a.from_date = "2026-10-01"
		a.base = 100000
		a.company = "Infiqo"
		submit(a)
		slip = make_salary_slip(ss.name, employee=emp, posting_date="2026-10-31")
		slip.start_date = "2026-10-01"
		slip.end_date = "2026-10-31"
		submit(slip)
		return f"{slip.name}: gross={slip.gross_pay}, net={slip.net_pay}, payment days={slip.payment_days}"

	step("Payroll: structure -> assignment -> Salary Slip for an employee", payroll)


# ---------------------------------------------------------------- Access control
def access():
	users = {
		"Aaliyan (dev)": "aaliyan.devs@gmail.com",
		"Ahmed (marketer)": "mohammadahmedhanfi@gmail.com",
		"Abdullah (manager)": "mabdullahazizawan@gmail.com",
		"Usman (HR)": "usmanzubairkhan9@gmail.com",
		"Yasir (COO)": "iamyasirmarwat@gmail.com",
		"Syed (founder)": "syedameenulhassanhamdani786@gmail.com",
	}
	checks = [("Sales Invoice", "create"), ("Quotation", "create"), ("Customer", "create"), ("Project", "read"), ("Timesheet", "create"), ("Leave Application", "create"), ("Salary Slip", "read"), ("Stock Entry", "create"), ("Purchase Order", "create"), ("CRM Lead", "create"), ("HD Ticket", "read"), ("Item", "create")]
	OUT.append("columns: " + ", ".join(f"{d}:{p}" for d, p in checks))
	for label, u in users.items():
		row = []
		for dt, p in checks:
			try:
				row.append("Y" if frappe.has_permission(dt, p, user=u) else "-")
			except Exception:
				row.append("?")
		frappe.set_user(u)
		try:
			emps = len(frappe.get_list("Employee"))
			cos = len(frappe.get_list("Company"))
		except Exception as e:
			emps, cos = f"err:{type(e).__name__}", "?"
		finally:
			frappe.set_user("Administrator")
		OUT.append(f"{label:20} {' '.join(row)}   | employees visible={emps}, companies visible={cos}")


# ---------------------------------------------------------------- Infrastructure
def infra():
	def fx():
		from erpnext.setup.utils import get_exchange_rate

		r = get_exchange_rate("USD", "PKR", nowdate())
		assert r and r > 100, r
		return f"live USD->PKR = {r}"

	step("Exchange rate auto-fetch from the internet", fx)

	def sched():
		from frappe.utils.scheduler import is_scheduler_disabled

		assert not is_scheduler_disabled()
		jobs = frappe.get_all("Scheduled Job Type", filters={"method": ["like", "%allocate_earned_leaves%"]}, fields=["method", "frequency", "stopped"])
		assert jobs and not jobs[0].stopped, jobs
		return f"scheduler on; earned-leave job: {jobs[0].frequency}"

	step("Scheduler on and monthly leave accrual job registered", sched)

	def cache():
		frappe.cache.set_value("tmp_func_test", "ok")
		assert frappe.cache.get_value("tmp_func_test") == "ok"
		frappe.cache.delete_value("tmp_func_test")
		return "redis cache read/write ok"

	step("Redis cache", cache)

	step("Shopify connector loads (not configured)", lambda: f"enabled={frappe.db.get_single_value('Shopify Setting', 'enable_shopify')}")
	OUT.append(f"INFO  email accounts that can send: {frappe.get_all('Email Account', filters={'enable_outgoing': 1}, pluck='name')}")


def run():
	section("UROOJJ: buy -> make -> test -> deliver -> invoice -> get paid", uroojj)
	section("INFIQO: sell, tax, deliver, track time, CRM, support", infiqo)
	section("HR: leave, attendance, payroll", hr)
	section("ACCESS CONTROL: what each person can actually do", access)
	section("INFRASTRUCTURE", infra)
	OUT.append(
		f"\nLEFTOVERS after rollback -> invoices={frappe.db.count('Sales Invoice')} stock entries={frappe.db.count('Stock Entry')} "
		f"projects={frappe.db.count('Project')} leave apps={frappe.db.count('Leave Application')} items={frappe.db.count('Item')} "
		f"naming counters used={frappe.get_all('Document Naming Rule', filters={'counter': ['>', 0]}, pluck='name')}"
	)
	with open("/tmp/func_report.txt", "w") as fh:
		fh.write("\n".join(OUT))
	print("WROTE")


def _default_currency():
	si = frappe.new_doc("Sales Invoice")
	si.company = "Infiqo"
	si.customer = "Nooria Travels"
	si.set_missing_values()
	assert si.currency == "PKR", si.currency
	return "new Infiqo invoice defaults to PKR"


_orig_infra = infra


def infra():  # noqa: F811
	step("New invoices default to PKR (not INR)", _default_currency)
	_orig_infra()
