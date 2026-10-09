import frappe

ABBR = {"Al Hamdan Enterprise": "AHE", "Infiqo": "INF", "Uroojj": "URJ"}

# Company-level default accounts that ERPNext's wizard normally selects. Without them
# every stock transaction (and any invoice rounding) fails with "set default ... account".
DEFAULTS = {
	"default_inventory_account": "Stock In Hand",
	"stock_adjustment_account": "Stock Adjustment",
	"stock_received_but_not_billed": "Stock Received But Not Billed",
	"default_expense_account": "Cost of Goods Sold",
	"round_off_account": "Round Off",
	"default_cash_account": "Cash",
	"write_off_account": "Write Off",
	"exchange_gain_loss_account": "Exchange Gain/Loss",
	"default_payroll_payable_account": "Payroll Payable",
}


def run():
	for company, abbr in ABBR.items():
		for field, account in DEFAULTS.items():
			full = f"{account} - {abbr}"
			if frappe.db.get_value("Company", company, field):
				continue
			if not frappe.db.exists("Account", full):
				print("missing account, skipped:", full)
				continue
			frappe.db.set_value("Company", company, field, full)
		if not frappe.db.get_value("Company", company, "round_off_cost_center"):
			frappe.db.set_value("Company", company, "round_off_cost_center", f"Main - {abbr}")
		print("defaults set for", company)

	# A "0 days after invoice" second installment gives two rows the same due date,
	# which ERPNext rejects outright, so the 50/50 template could not be used at all.
	# 30 days is a placeholder for "balance on delivery" -- the user should adjust it.
	frappe.db.set_value("Payment Term", "Infiqo - 50% on Delivery", "credit_days", 30)
	frappe.db.sql(
		"update `tabPayment Terms Template Detail` set credit_days = 30 where payment_term = %s",
		"Infiqo - 50% on Delivery",
	)

	# Monthly earned-leave accrual, auto backups and queued jobs only run with the scheduler on.
	from frappe.utils.scheduler import enable_scheduler

	enable_scheduler()

	frappe.db.commit()
	frappe.clear_cache()
	print("DONE")
