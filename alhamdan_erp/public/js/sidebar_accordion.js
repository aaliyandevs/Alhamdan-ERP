// Sidebar behavior for the 3 company pages (Al Hamdan Enterprise, Infiqo, Uroojj):
//   1. Accordion: opening one top-level section (Sales, Purchasing, Accounts, etc.)
//      closes whatever other section was open.
//   2. No memory across visits: every time you switch to a company, that company's
//      sidebar always starts fully closed -- it never remembers a section you left
//      open from a previous visit, so there's nothing left open behind you either.
// Core Frappe has neither behavior for Workspace Sidebar sections, so both are
// patched onto the shared sidebar classes here.
frappe.provide("frappe.ui.sidebar_item");

(function patch_sidebar_behavior() {
	const COMPANY_SIDEBAR_TITLES = ["al hamdan enterprise", "infiqo", "uroojj"];

	function forget_remembered_state(workspace_title) {
		const key = workspace_title && String(workspace_title).toLowerCase();
		if (!key || !COMPANY_SIDEBAR_TITLES.includes(key)) return;
		try {
			const raw = localStorage.getItem("section-breaks-state");
			if (!raw) return;
			const state = JSON.parse(raw);
			if (state[key]) {
				delete state[key];
				localStorage.setItem("section-breaks-state", JSON.stringify(state));
			}
		} catch (e) {
			// malformed/blocked storage -- nothing to clean up, fall through
		}
	}

	function apply() {
		const SectionBreak = frappe.ui.sidebar_item && frappe.ui.sidebar_item.TypeSectionBreak;
		const Sidebar = frappe.ui.Sidebar;
		if (!SectionBreak || !Sidebar || SectionBreak.prototype.__alhamdan_sidebar_patched) {
			return;
		}

		// (1) Accordion -- after a section finishes opening, close every other open one.
		const original_toggle = SectionBreak.prototype.toggle;
		SectionBreak.prototype.toggle = function () {
			original_toggle.call(this);
			if (!this.collapsed) {
				(frappe.app.sidebar && frappe.app.sidebar.items ? frappe.app.sidebar.items : []).forEach(
					(other) => {
						if (
							other !== this &&
							other.item &&
							other.item.type === "Section Break" &&
							other.collapsed === false
						) {
							other.close();
						}
					}
				);
			}
		};

		// (2) No cross-visit memory -- wipe this company's saved open/closed state
		// right before its sidebar is (re)built, so keep_closed always wins.
		const original_setup = Sidebar.prototype.setup;
		Sidebar.prototype.setup = function (workspace_title) {
			forget_remembered_state(workspace_title);
			return original_setup.call(this, workspace_title);
		};

		SectionBreak.prototype.__alhamdan_sidebar_patched = true;
	}

	// sidebar.js loads as part of the same desk bundle, but apply defensively in
	// case of load-order changes: patch now if available, and again once the app
	// is ready (frappe.ui.Sidebar / sidebar_item are always defined by then).
	apply();
	$(document).on("app_ready", apply);
})();
