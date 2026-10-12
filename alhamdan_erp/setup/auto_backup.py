import frappe
from frappe.utils.backups import scheduled_backup


def run():
	"""Daily backup via the in-app scheduler (see hooks.py for why: no system cron daemon
	runs in this dev container, so `bench setup backups` has nothing to execute). Keeps the
	last `System Settings.backup_limit` backups (default 3); skips if the last backup is
	under 6 hours old."""
	try:
		scheduled_backup(ignore_files=False)
		frappe.logger().info("alhamdan_erp.auto_backup: completed")
	except Exception:
		frappe.log_error(title="alhamdan_erp.auto_backup failed")
		raise
