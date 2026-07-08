import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

import repositories as repo
import validators as v
import security as sec

BRANCHES = ["Bristol", "Cardiff", "London", "Manchester"]
ROLES = ["FrontDeskStaff", "FinanceManager", "MaintenanceStaff", "Administrator", "Manager"]
STUDY_LEVELS = ["Undergraduate", "Masters", "PhD"]


class PamsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Paragon Apartment Management System (PAMS)")
        self.geometry("960x620")
        self.minsize(860, 560)
        self.current_user = None

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.user_repo = repo.UserRepository()
        self.tenant_repo = repo.TenantRepository()
        self.apartment_repo = repo.ApartmentRepository()
        self.lease_repo = repo.LeaseRepository()
        self.maintenance_repo = repo.MaintenanceRepository()
        self.billing_repo = repo.BillingRepository()
        self.report_repo = repo.ReportRepository()

        self.show_login()

    def clear(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_login(self):
        self.current_user = None
        self.clear()
        frame = tk.Frame(self.container, padx=40, pady=40)
        frame.pack(expand=True)

        tk.Label(frame, text="PAMS Login", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 20)
        )
        tk.Label(frame, text="Username").grid(row=1, column=0, sticky="e", pady=6)
        username_entry = tk.Entry(frame, width=28)
        username_entry.grid(row=1, column=1, pady=6)

        tk.Label(frame, text="Password").grid(row=2, column=0, sticky="e", pady=6)
        password_entry = tk.Entry(frame, width=28, show="*")
        password_entry.grid(row=2, column=1, pady=6)

        def attempt_login(event=None):
            user = self.user_repo.authenticate(
                username_entry.get().strip(), password_entry.get()
            )
            if user is None:
                messagebox.showerror("Login failed", "Invalid username or password.")
                return
            self.current_user = user
            self.show_dashboard()

        password_entry.bind("<Return>", attempt_login)
        tk.Button(frame, text="Log in", width=14, command=attempt_login).grid(
            row=3, column=0, columnspan=2, pady=(16, 4)
        )


    #  Dashboard 

    def show_dashboard(self):
        self.clear()
        root = tk.Frame(self.container)
        root.pack(fill="both", expand=True)

        sidebar = tk.Frame(root, width=200, bg="#1d3557")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, bg="#1d3557", fg="white",
            text=f"{self.current_user.full_name}\n{self.current_user.role}\n"
                 f"{self.current_user.branch_location}",
            justify="left", font=("Segoe UI", 10, "bold"), pady=16
        ).pack(fill="x", padx=10)

        self.content = tk.Frame(root, padx=16, pady=16)
        self.content.pack(side="right", fill="both", expand=True)

        actions = self._menu_for_role(self.current_user.role)
        for label, handler in actions:
            tk.Button(sidebar, text=label, anchor="w", relief="flat",
                      bg="#457b9d", fg="white", activebackground="#1d3557",
                      command=handler).pack(fill="x", padx=10, pady=4)

        tk.Button(sidebar, text="Log out", anchor="w", relief="flat",
                  bg="#e63946", fg="white", command=self.show_login).pack(
            fill="x", padx=10, pady=(30, 4)
        )

        actions[0][1]()  # show first screen by default

    def _menu_for_role(self, role):
        if role == "FrontDeskStaff":
            return [
                ("Register tenant", self.screen_register_tenant),
                ("Tenant list", self.screen_tenant_list),
                ("Assign apartment / lease", self.screen_assign_apartment),
                ("Log maintenance request", self.screen_log_maintenance),
                ("Apartments", self.screen_apartment_list),
            ]
        if role == "FinanceManager":
            return [
                ("Generate invoice", self.screen_generate_invoice),
                ("Record payment", self.screen_record_payment),
                ("Invoices", self.screen_invoice_list),
                ("Financial report", self.screen_financial_report),
            ]
        if role == "MaintenanceStaff":
            return [
                ("Open requests", self.screen_maintenance_open),
                ("Resolve request", self.screen_resolve_maintenance),
            ]
        if role == "Administrator":
            return [
                ("Manage apartments", self.screen_apartment_admin),
                ("Manage users", self.screen_user_admin),
                ("Lease tracking", self.screen_lease_tracking),
                ("Branch report", self.screen_branch_report),
            ]
        if role == "Manager":
            return [
                ("Occupancy report", self.screen_occupancy_report),
                ("Financial report", self.screen_financial_report),
                ("Apartments (all branches)", self.screen_apartment_list),
                ("Expand to new city", self.screen_expand_city),
            ]
        return []

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    #  shared widgets 

    def _make_treeview(self, parent, columns, rows, widths=None):
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=16)
        for i, col in enumerate(columns):
            tree.heading(col, text=col)
            tree.column(col, width=(widths[i] if widths else 120), anchor="w")
        for row in rows:
            tree.insert("", "end", values=row)
        tree.pack(fill="both", expand=True, pady=8)
        return tree

    def _error(self, exc):
        messagebox.showerror("Error", str(exc))

    #  Front-desk screens 

    def screen_register_tenant(self):
        self.clear_content()
        tk.Label(self.content, text="Register tenant", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        form = tk.Frame(self.content, pady=10)
        form.pack(anchor="w")

        fields = {}
        labels = ["NI number (e.g. AB123456C)", "Full name", "Phone", "Email",
                  "Occupation", "References"]
        keys = ["ni", "name", "phone", "email", "occupation", "refs"]
        for i, (label, key) in enumerate(zip(labels, keys)):
            tk.Label(form, text=label).grid(row=i, column=0, sticky="e", pady=3)
            e = tk.Entry(form, width=32)
            e.grid(row=i, column=1, pady=3)
            fields[key] = e

        is_student_var = tk.BooleanVar()
        tk.Checkbutton(form, text="Student applicant", variable=is_student_var).grid(
            row=len(labels), column=1, sticky="w"
        )

        tk.Label(form, text="Study level").grid(row=len(labels) + 1, column=0, sticky="e")
        study_level_var = tk.StringVar(value=STUDY_LEVELS[0])
        ttk.Combobox(form, textvariable=study_level_var, values=STUDY_LEVELS,
                     state="readonly", width=29).grid(row=len(labels) + 1, column=1)

        tk.Label(form, text="Offer letter ref").grid(row=len(labels) + 2, column=0, sticky="e")
        offer_entry = tk.Entry(form, width=32)
        offer_entry.grid(row=len(labels) + 2, column=1, pady=3)

        def submit():
            try:
                tenant = self.tenant_repo.register_tenant(
                    ni_number=fields["ni"].get(),
                    full_name=fields["name"].get(),
                    phone=fields["phone"].get(),
                    email=fields["email"].get(),
                    occupation=fields["occupation"].get(),
                    references_info=fields["refs"].get(),
                    branch_location=self.current_user.branch_location,
                    is_student=is_student_var.get(),
                    study_level=study_level_var.get() if is_student_var.get() else None,
                    offer_letter_ref=offer_entry.get() if is_student_var.get() else None,
                    current_user=self.current_user,
                )
                messagebox.showinfo("Success", f"Tenant registered (ID {tenant.tenant_id}).")
                self.screen_register_tenant()
            except (v.ValidationError, sec.PermissionError_) as e:
                self._error(e)

        tk.Button(form, text="Register", command=submit).grid(
            row=len(labels) + 3, column=1, sticky="w", pady=10
        )

    def screen_tenant_list(self):
        self.clear_content()
        tk.Label(self.content, text="Tenants", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        rows = self.tenant_repo.list_tenants()
        data = [(r["tenant_id"], r["full_name"], r["ni_number"], r["email"],
                 "Yes" if r["is_student"] else "No", r["branch_location"])
                for r in rows]
        self._make_treeview(
            self.content, ["ID", "Name", "NI number", "Email", "Student", "Branch"],
            data, widths=[40, 150, 110, 180, 60, 100]
        )

    def screen_assign_apartment(self):
        self.clear_content()
        tk.Label(self.content, text="Assign apartment / create lease",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        form = tk.Frame(self.content, pady=10)
        form.pack(anchor="w")

        tk.Label(form, text="Tenant ID").grid(row=0, column=0, sticky="e", pady=3)
        tenant_id_entry = tk.Entry(form, width=20)
        tenant_id_entry.grid(row=0, column=1, pady=3)

        tk.Label(form, text="Apartment ID").grid(row=1, column=0, sticky="e", pady=3)
        apt_id_entry = tk.Entry(form, width=20)
        apt_id_entry.grid(row=1, column=1, pady=3)

        tk.Label(form, text="Start date (YYYY-MM-DD)").grid(row=2, column=0, sticky="e", pady=3)
        start_entry = tk.Entry(form, width=20)
        start_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        start_entry.grid(row=2, column=1, pady=3)

        tk.Label(form, text="End date (YYYY-MM-DD)").grid(row=3, column=0, sticky="e", pady=3)
        end_entry = tk.Entry(form, width=20)
        end_entry.grid(row=3, column=1, pady=3)

        def submit():
            try:
                lease = self.lease_repo.create_lease(
                    int(tenant_id_entry.get()), int(apt_id_entry.get()),
                    start_entry.get(), end_entry.get(), current_user=self.current_user
                )
                messagebox.showinfo("Success", f"Lease created (ID {lease.lease_id}).")
            except (v.ValidationError, sec.PermissionError_, ValueError) as e:
                self._error(e)

        tk.Button(form, text="Create lease", command=submit).grid(
            row=4, column=1, sticky="w", pady=10
        )
        tk.Label(self.content, text="Tip: check Apartments / Tenants tabs for valid IDs.",
                 fg="grey").pack(anchor="w")

    def screen_log_maintenance(self):
        self.clear_content()
        tk.Label(self.content, text="Log maintenance request",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        form = tk.Frame(self.content, pady=10)
        form.pack(anchor="w")

        tk.Label(form, text="Tenant ID").grid(row=0, column=0, sticky="e", pady=3)
        tenant_id_entry = tk.Entry(form, width=20)
        tenant_id_entry.grid(row=0, column=1, pady=3)

        tk.Label(form, text="Apartment ID").grid(row=1, column=0, sticky="e", pady=3)
        apt_id_entry = tk.Entry(form, width=20)
        apt_id_entry.grid(row=1, column=1, pady=3)

        tk.Label(form, text="Description").grid(row=2, column=0, sticky="e", pady=3)
        desc_entry = tk.Entry(form, width=32)
        desc_entry.grid(row=2, column=1, pady=3)

        tk.Label(form, text="Priority").grid(row=3, column=0, sticky="e", pady=3)
        priority_var = tk.StringVar(value="medium")
        ttk.Combobox(form, textvariable=priority_var, values=["low", "medium", "high"],
                     state="readonly", width=29).grid(row=3, column=1, pady=3)

        def submit():
            try:
                req = self.maintenance_repo.log_request(
                    int(tenant_id_entry.get()), int(apt_id_entry.get()),
                    desc_entry.get(), priority_var.get(), current_user=self.current_user
                )
                messagebox.showinfo("Success", f"Request logged (ID {req.request_id}).")
            except (v.ValidationError, sec.PermissionError_, ValueError) as e:
                self._error(e)

        tk.Button(form, text="Submit", command=submit).grid(row=4, column=1, sticky="w", pady=10)

    def screen_apartment_list(self):
        self.clear_content()
        tk.Label(self.content, text="Apartments", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        rows = self.apartment_repo.list_apartments()
        data = [(r["apartment_id"], r["branch_location"], r["apartment_type"],
                 f"£{r['monthly_rent']:.2f}", r["num_rooms"],
                 "Yes" if r["student_eligible"] else "No", r["status"])
                for r in rows]
        self._make_treeview(
            self.content, ["ID", "Branch", "Type", "Rent", "Rooms", "Student?", "Status"],
            data, widths=[40, 100, 140, 90, 60, 70, 90]
        )

    #  Finance screens 

    def screen_generate_invoice(self):
        self.clear_content()
        tk.Label(self.content, text="Generate invoice", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        form = tk.Frame(self.content, pady=10)
        form.pack(anchor="w")

        tk.Label(form, text="Lease ID").grid(row=0, column=0, sticky="e", pady=3)
        lease_id_entry = tk.Entry(form, width=20)
        lease_id_entry.grid(row=0, column=1, pady=3)

        tk.Label(form, text="Due date (YYYY-MM-DD)").grid(row=1, column=0, sticky="e", pady=3)
        due_entry = tk.Entry(form, width=20)
        due_entry.grid(row=1, column=1, pady=3)

        def submit():
            try:
                inv = self.billing_repo.generate_invoice(
                    int(lease_id_entry.get()), due_entry.get(), current_user=self.current_user
                )
                messagebox.showinfo(
                    "Invoice created",
                    f"Invoice #{inv.invoice_id} for £{inv.amount:.2f}, due {inv.due_date}."
                )
            except (v.ValidationError, sec.PermissionError_, ValueError) as e:
                self._error(e)

        tk.Button(form, text="Generate", command=submit).grid(row=2, column=1, sticky="w", pady=10)

    def screen_record_payment(self):
        self.clear_content()
        tk.Label(self.content, text="Record payment", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        form = tk.Frame(self.content, pady=10)
        form.pack(anchor="w")

        tk.Label(form, text="Invoice ID").grid(row=0, column=0, sticky="e", pady=3)
        invoice_id_entry = tk.Entry(form, width=20)
        invoice_id_entry.grid(row=0, column=1, pady=3)

        tk.Label(form, text="Amount").grid(row=1, column=0, sticky="e", pady=3)
        amount_entry = tk.Entry(form, width=20)
        amount_entry.grid(row=1, column=1, pady=3)

        tk.Label(form, text="Method").grid(row=2, column=0, sticky="e", pady=3)
        method_var = tk.StringVar(value="bank_transfer")
        ttk.Combobox(form, textvariable=method_var,
                     values=["bank_transfer", "card", "cash"], state="readonly",
                     width=18).grid(row=2, column=1, pady=3, sticky="w")

        def submit():
            try:
                payment = self.billing_repo.record_payment(
                    int(invoice_id_entry.get()), amount_entry.get(),
                    method_var.get(), current_user=self.current_user
                )
                messagebox.showinfo(
                    "Payment recorded",
                    f"Receipt #{payment.payment_id}: £{payment.amount:.2f} on "
                    f"{payment.payment_date} via {payment.method}."
                )
            except (v.ValidationError, sec.PermissionError_, ValueError) as e:
                self._error(e)

        tk.Button(form, text="Record payment", command=submit).grid(
            row=3, column=1, sticky="w", pady=10
        )

    def screen_invoice_list(self):
        self.clear_content()
        tk.Label(self.content, text="Invoices", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        self.billing_repo.refresh_late_invoices()
        rows = self.billing_repo.list_invoices()
        data = [(r["invoice_id"], r["lease_id"], f"£{r['amount']:.2f}",
                 r["issue_date"], r["due_date"], r["status"]) for r in rows]
        self._make_treeview(
            self.content, ["ID", "Lease ID", "Amount", "Issued", "Due", "Status"],
            data, widths=[40, 70, 90, 100, 100, 80]
        )

    def screen_financial_report(self):
        self.clear_content()
        tk.Label(self.content, text="Financial summary", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        try:
            summary = self.report_repo.financial_summary(current_user=self.current_user)
        except sec.PermissionError_ as e:
            self._error(e)
            return
        text = (
            f"Collected rent:      £{summary['collected_rent']:.2f}\n"
            f"Pending rent:        £{summary['pending_rent']:.2f}\n"
            f"Maintenance costs:   £{summary['maintenance_cost']:.2f}"
        )
        tk.Label(self.content, text=text, font=("Consolas", 12), justify="left",
                 pady=20).pack(anchor="w")

    #  Maintenance screens 

    def screen_maintenance_open(self):
        self.clear_content()
        tk.Label(self.content, text="Open / scheduled requests",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        rows = [r for r in self.maintenance_repo.list_requests() if r["status"] != "resolved"]
        data = [(r["request_id"], r["tenant_id"], r["apartment_id"], r["description"],
                 r["priority"], r["reported_date"], r["status"]) for r in rows]
        self._make_treeview(
            self.content, ["ID", "Tenant", "Apt", "Description", "Priority", "Reported", "Status"],
            data, widths=[40, 60, 50, 220, 70, 100, 80]
        )

    def screen_resolve_maintenance(self):
        self.clear_content()
        tk.Label(self.content, text="Resolve maintenance request",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        form = tk.Frame(self.content, pady=10)
        form.pack(anchor="w")

        tk.Label(form, text="Request ID").grid(row=0, column=0, sticky="e", pady=3)
        req_id_entry = tk.Entry(form, width=20)
        req_id_entry.grid(row=0, column=1, pady=3)

        tk.Label(form, text="Resolved date (YYYY-MM-DD)").grid(row=1, column=0, sticky="e", pady=3)
        resolved_entry = tk.Entry(form, width=20)
        resolved_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        resolved_entry.grid(row=1, column=1, pady=3)

        tk.Label(form, text="Total cost (£)").grid(row=2, column=0, sticky="e", pady=3)
        cost_entry = tk.Entry(form, width=20)
        cost_entry.grid(row=2, column=1, pady=3)

        tk.Label(form, text="Time taken (hours)").grid(row=3, column=0, sticky="e", pady=3)
        hours_entry = tk.Entry(form, width=20)
        hours_entry.grid(row=3, column=1, pady=3)

        def submit():
            try:
                share = self.maintenance_repo.resolve_request(
                    int(req_id_entry.get()), resolved_entry.get(),
                    cost_entry.get(), hours_entry.get(), current_user=self.current_user
                )
                messagebox.showinfo(
                    "Resolved", f"Request resolved. Tenant share: £{share:.2f}"
                )
            except (v.ValidationError, sec.PermissionError_, ValueError) as e:
                self._error(e)

        tk.Button(form, text="Resolve", command=submit).grid(row=4, column=1, sticky="w", pady=10)

    #  Administrator screens 

    def screen_apartment_admin(self):
        self.clear_content()
        tk.Label(self.content, text="Manage apartments", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        form = tk.Frame(self.content, pady=10)
        form.pack(anchor="w")

        tk.Label(form, text="Branch").grid(row=0, column=0, sticky="e", pady=3)
        branch_var = tk.StringVar(value=self.current_user.branch_location)
        ttk.Combobox(form, textvariable=branch_var, values=BRANCHES, state="readonly",
                     width=29).grid(row=0, column=1, pady=3)

        tk.Label(form, text="Type (e.g. Two-bedroom house)").grid(row=1, column=0, sticky="e", pady=3)
        type_entry = tk.Entry(form, width=32)
        type_entry.grid(row=1, column=1, pady=3)

        tk.Label(form, text="Monthly rent (£)").grid(row=2, column=0, sticky="e", pady=3)
        rent_entry = tk.Entry(form, width=32)
        rent_entry.grid(row=2, column=1, pady=3)

        tk.Label(form, text="Number of rooms").grid(row=3, column=0, sticky="e", pady=3)
        rooms_entry = tk.Entry(form, width=32)
        rooms_entry.grid(row=3, column=1, pady=3)

        student_var = tk.BooleanVar()
        tk.Checkbutton(form, text="Available to students", variable=student_var).grid(
            row=4, column=1, sticky="w"
        )

        def submit():
            try:
                apt = self.apartment_repo.add_apartment(
                    branch_var.get(), type_entry.get(), rent_entry.get(),
                    rooms_entry.get(), student_var.get(), current_user=self.current_user
                )
                messagebox.showinfo("Success", f"Apartment added (ID {apt.apartment_id}).")
                self.screen_apartment_admin()
            except (v.ValidationError, sec.PermissionError_) as e:
                self._error(e)

        tk.Button(form, text="Add apartment", command=submit).grid(
            row=5, column=1, sticky="w", pady=10
        )
        self.screen_apartment_list_inline()

    def screen_apartment_list_inline(self):
        rows = self.apartment_repo.list_apartments()
        data = [(r["apartment_id"], r["branch_location"], r["apartment_type"],
                 f"£{r['monthly_rent']:.2f}", r["status"]) for r in rows]
        self._make_treeview(
            self.content, ["ID", "Branch", "Type", "Rent", "Status"], data,
            widths=[40, 100, 140, 90, 90]
        )

    def screen_user_admin(self):
        self.clear_content()
        tk.Label(self.content, text="Manage users", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        form = tk.Frame(self.content, pady=10)
        form.pack(anchor="w")

        labels = ["Username", "Password", "Full name", "Email"]
        keys = ["username", "password", "full_name", "email"]
        entries = {}
        for i, (label, key) in enumerate(zip(labels, keys)):
            tk.Label(form, text=label).grid(row=i, column=0, sticky="e", pady=3)
            e = tk.Entry(form, width=32, show="*" if key == "password" else "")
            e.grid(row=i, column=1, pady=3)
            entries[key] = e

        tk.Label(form, text="Role").grid(row=4, column=0, sticky="e", pady=3)
        role_var = tk.StringVar(value=ROLES[0])
        ttk.Combobox(form, textvariable=role_var, values=ROLES, state="readonly",
                     width=29).grid(row=4, column=1, pady=3)

        tk.Label(form, text="Branch").grid(row=5, column=0, sticky="e", pady=3)
        branch_var = tk.StringVar(value=self.current_user.branch_location)
        ttk.Combobox(form, textvariable=branch_var, values=BRANCHES, state="readonly",
                     width=29).grid(row=5, column=1, pady=3)

        def submit():
            try:
                user = self.user_repo.create_user(
                    entries["username"].get(), entries["password"].get(),
                    entries["full_name"].get(), entries["email"].get(),
                    role_var.get(), branch_var.get(), current_user=self.current_user
                )
                messagebox.showinfo("Success", f"User created: {user.username}")
                self.screen_user_admin()
            except (v.ValidationError, sec.PermissionError_) as e:
                self._error(e)

        tk.Button(form, text="Create user", command=submit).grid(
            row=6, column=1, sticky="w", pady=10
        )

        rows = self.user_repo.list_users()
        data = [(r["user_id"], r["username"], r["role"], r["branch_location"],
                 "Active" if r["is_active"] else "Disabled") for r in rows]
        self._make_treeview(
            self.content, ["ID", "Username", "Role", "Branch", "Status"], data,
            widths=[40, 140, 130, 100, 70]
        )

    def screen_lease_tracking(self):
        self.clear_content()
        tk.Label(self.content, text="Lease tracking", font=("Segoe UI", 14, "bold")).pack(anchor="w")
        rows = self.lease_repo.list_leases()
        data = [(r["lease_id"], r["tenant_name"], r["apartment_type"],
                 r["branch_location"], r["start_date"], r["end_date"], r["status"])
                for r in rows]
        self._make_treeview(
            self.content, ["ID", "Tenant", "Apartment", "Branch", "Start", "End", "Status"],
            data, widths=[40, 140, 140, 100, 100, 100, 80]
        )

        term_form = tk.Frame(self.content, pady=10)
        term_form.pack(anchor="w")
        tk.Label(term_form, text="Terminate lease early - Lease ID").grid(row=0, column=0)
        lease_id_entry = tk.Entry(term_form, width=10)
        lease_id_entry.grid(row=0, column=1, padx=4)
        tk.Label(term_form, text="Termination date").grid(row=0, column=2)
        term_date_entry = tk.Entry(term_form, width=14)
        term_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        term_date_entry.grid(row=0, column=3, padx=4)

        def terminate():
            try:
                penalty, enough_notice = self.lease_repo.terminate_lease_early(
                    int(lease_id_entry.get()), term_date_entry.get(),
                    current_user=self.current_user
                )
                note = "" if enough_notice else " (less than 1 month notice given)"
                messagebox.showinfo(
                    "Lease terminated", f"Penalty due: £{penalty:.2f}{note}"
                )
                self.screen_lease_tracking()
            except (v.ValidationError, ValueError) as e:
                self._error(e)

        tk.Button(term_form, text="Terminate", command=terminate).grid(row=0, column=4, padx=8)

    def screen_branch_report(self):
        self.clear_content()
        tk.Label(self.content, text=f"Branch report — {self.current_user.branch_location}",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        rows = self.apartment_repo.list_apartments(
            branch_location=self.current_user.branch_location
        )
        data = [(r["apartment_id"], r["apartment_type"], f"£{r['monthly_rent']:.2f}",
                 r["status"]) for r in rows]
        self._make_treeview(
            self.content, ["ID", "Type", "Rent", "Status"], data, widths=[60, 160, 100, 100]
        )

    #  Manager screens 

    def screen_occupancy_report(self):
        self.clear_content()
        tk.Label(self.content, text="Occupancy report (all branches)",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        try:
            rows = self.report_repo.occupancy_report(current_user=self.current_user)
        except sec.PermissionError_ as e:
            self._error(e)
            return
        data = [(r["branch_location"], r["status"], r["total"]) for r in rows]
        self._make_treeview(
            self.content, ["Branch", "Status", "Count"], data, widths=[140, 120, 80]
        )

    def screen_expand_city(self):
        self.clear_content()
        tk.Label(self.content, text="Expand to a new city",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(
            self.content,
            text="This is a placeholder workflow: in a full release this screen would\n"
                 "create a new branch_location entry and provision an Administrator\n"
                 "account for it. Currently supported branches are:\n"
                 f"{', '.join(BRANCHES)}",
            justify="left", pady=20
        ).pack(anchor="w")


if __name__ == "__main__":
    PamsApp().mainloop()
