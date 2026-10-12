import frappe

# Map each existing user to the Role Profile that matches (or now will match) their
# actual access, so future hires are "assign one profile" instead of re-deriving roles.
# Where a user's current roles are broader than the matching profile defined, the profile
# is extended to the union first -- applying it must never take access away silently.
USER_PROFILE = {
	"syedameenulhassanhamdani786@gmail.com": "Group Admin",
	"iamyasirmarwat@gmail.com": "Group Admin",
	"usmanzubairkhan9@gmail.com": "Group HR",
	"mabdullahazizawan@gmail.com": "Infiqo - Manager",
	"aaliyan.devs@gmail.com": "Infiqo - Delivery",
	"arifsabzali6@gmail.com": "Infiqo - Delivery",
	"mohammadahmedhanfi@gmail.com": "Infiqo - Sales/Accounts",
}

def run():
	for user, profile in USER_PROFILE.items():
		if not frappe.db.exists("User", user):
			print("skipped, no such user:", user)
			continue
		udoc = frappe.get_doc("User", user)
		current_roles = {r.role for r in udoc.roles}

		pdoc = frappe.get_doc("Role Profile", profile)
		profile_roles = {r.role for r in pdoc.roles}

		missing_in_profile = current_roles - profile_roles
		if missing_in_profile:
			for role in missing_in_profile:
				pdoc.append("roles", {"role": role})
			pdoc.save(ignore_permissions=True)
			print(f"extended {profile} with: {sorted(missing_in_profile)}")

		# `role_profile_name` is deprecated in this Frappe version; `role_profiles` (plural,
		# TableMultiSelect) is the live field. Setting it alone does nothing to user.roles --
		# populate_role_profile_roles() is the method that actually syncs, and it REPLACES
		# self.roles with the profile's role set (not a merge), which is why the profile was
		# extended to the union above first.
		if not any(r.role_profile == profile for r in udoc.role_profiles):
			udoc.append("role_profiles", {"role_profile": profile})
		udoc.populate_role_profile_roles()
		udoc.save(ignore_permissions=True)
		print(f"{user} -> role_profiles={[r.role_profile for r in udoc.role_profiles]}")

	frappe.db.commit()

	for user, profile in USER_PROFILE.items():
		if not frappe.db.exists("User", user):
			continue
		doc = frappe.get_doc("User", user)
		roles = sorted(r.role for r in doc.roles)
		profiles = [r.role_profile for r in doc.role_profiles]
		print(f"{user}: role_profiles={profiles}, roles={roles}")
	print("DONE")
