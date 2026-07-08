import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont
from datetime import date

import repositories as repo
import validators as v
import security as sec

BRANCHES = ["Bristol", "Cardiff", "London", "Manchester"]
ROLES = ["FrontDeskStaff", "FinanceManager", "MaintenanceStaff", "Administrator", "Manager"]
STUDY_LEVELS = ["Undergraduate", "Masters", "PhD"]

LIGHT_THEME = {
    "bg": "#f5f5f5",
    "fg": "#1a1a1a",
    "entry_bg": "#ffffff",
    "entry_fg": "#1a1a1a",
    "button_bg": "#e1e1e1",
    "button_fg": "#1a1a1a",
    "active_bg": "#d5d5d5",
    "panel_bg": "#1d3557",
    "panel_fg": "#ffffff",
    "menu_button_bg": "#457b9d",
    "menu_button_fg": "#ffffff",
    "menu_button_active_bg": "#1d3557",
    "logout_bg": "#e63946",
    "logout_fg": "#ffffff",
    "toggle_bg": "#a8dadc",
    "toggle_fg": "#1d3557",
    "muted": "#6c6c6c",
    "tree_bg": "#ffffff",
    "tree_fg": "#1a1a1a",
    "tree_heading_bg": "#e6e6e6",
    "tree_select_bg": "#457b9d",
}

DARK_THEME = {
    "bg": "#1e1e2e",
    "fg": "#e8e8e8",
    "entry_bg": "#2b2b3d",
    "entry_fg": "#f0f0f0",
    "button_bg": "#3a3a4d",
    "button_fg": "#f0f0f0",
    "active_bg": "#4a4a60",
    "panel_bg": "#11111b",
    "panel_fg": "#f0f0f0",
    "menu_button_bg": "#2c3e6b",
    "menu_button_fg": "#f0f0f0",
    "menu_button_active_bg": "#11111b",
    "logout_bg": "#b83244",
    "logout_fg": "#ffffff",
    "toggle_bg": "#3a3a4d",
    "toggle_fg": "#f0f0f0",
    "muted": "#9a9aa5",
    "tree_bg": "#26263a",
    "tree_fg": "#f0f0f0",
    "tree_heading_bg": "#33334a",
    "tree_select_bg": "#3d5a80",
}


class PamsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Paragon Apartment Management System (PAMS)")
        self.geometry("960x620")
        self.minsize(860, 560)
        self.current_user = None
        self.current_screen = None
        self.dark_mode = False
        self.theme = LIGHT_THEME

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.apply_theme()

        # Text size scaling
        self.font_scale_delta = 0
        self.font_min_delta = -3
        self.font_max_delta = 5
        self.BASE_FONT_SIZES = {
            "TkDefaultFont": 10,
            "TkTextFont": 10,
            "TkHeadingFont": 10,
            "TkMenuFont": 10,
            "TkFixedFont": 10,
        }
        self._named_fonts = {}
        for name, base_size in self.BASE_FONT_SIZES.items():
            try:
                f = tkfont.nametofont(name)
                f.configure(size=base_size)
                self._named_fonts[name] = f
            except tk.TclError:
                pass

        self.font_title = tkfont.Font(family="Segoe UI", size=18, weight="bold")
        self.font_heading = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.font_sidebar = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self.font_mono = tkfont.Font(family="Consolas", size=12)
        self.apply_font_scale()

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

    #  Theming 

    def apply_theme(self):
        theme = DARK_THEME if self.dark_mode else LIGHT_THEME
        self.theme = theme

        self.configure(bg=theme["bg"])
        self.container.configure(bg=theme["bg"])

        self.option_add("*Background", theme["bg"])
        self.option_add("*Foreground", theme["fg"])
        self.option_add("*activeBackground", theme["active_bg"])
        self.option_add("*activeForeground", theme["fg"])
        self.option_add("*Entry.background", theme["entry_bg"])
        self.option_add("*Entry.foreground", theme["entry_fg"])
        self.option_add("*Entry.insertBackground", theme["entry_fg"])
        self.option_add("*Button.background", theme["button_bg"])
        self.option_add("*Button.foreground", theme["button_fg"])
        self.option_add("*Checkbutton.background", theme["bg"])
        self.option_add("*Checkbutton.foreground", theme["fg"])
        self.option_add("*Checkbutton.selectColor", theme["entry_bg"])

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Treeview", background=theme["tree_bg"], fieldbackground=theme["tree_bg"],
            foreground=theme["tree_fg"], bordercolor=theme["tree_heading_bg"]
        )
        style.map(
            "Treeview", background=[("selected", theme["tree_select_bg"])],
            foreground=[("selected", "#ffffff")]
        )
        style.configure(
            "Treeview.Heading", background=theme["tree_heading_bg"], foreground=theme["fg"],
            relief="flat"
        )
        style.map("Treeview.Heading", background=[("active", theme["tree_heading_bg"])])
        style.configure(
            "TCombobox", fieldbackground=theme["entry_bg"], background=theme["entry_bg"],
            foreground=theme["entry_fg"], arrowcolor=theme["fg"]
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme["entry_bg"])],
            foreground=[("readonly", theme["entry_fg"])],
        )

    #  Text size 

    def apply_font_scale(self):
        delta = self.font_scale_delta
        for name, f in self._named_fonts.items():
            f.configure(size=self.BASE_FONT_SIZES[name] + delta)
        self.font_title.configure(size=18 + delta)
        self.font_heading.configure(size=14 + delta)
        self.font_sidebar.configure(size=10 + delta)
        self.font_mono.configure(size=12 + delta)

    def increase_font_size(self):
        if self.font_scale_delta < self.font_max_delta:
            self.font_scale_delta += 1
            self.apply_font_scale()

    def decrease_font_size(self):
        if self.font_scale_delta > self.font_min_delta:
            self.font_scale_delta -= 1
            self.apply_font_scale()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        if self.current_user is None:
            self.show_login()
        else:
            self.show_dashboard(preserve_screen=True)

    def _nav(self, handler):
        def _go():
            self.current_screen = handler
            handler()
        return _go

    def show_login(self):
        self.current_user = None
        self.current_screen = None
        self.clear()
        theme = self.theme
        frame = tk.Frame(self.container, padx=40, pady=40, bg=theme["bg"])
        frame.pack(expand=True)

        tk.Label(frame, text="PAMS Login", font=self.font_title,
                 bg=theme["bg"], fg=theme["fg"]).grid(
            row=0, column=0, columnspan=2, pady=(0, 20)
        )
        tk.Label(frame, text="Username", bg=theme["bg"], fg=theme["fg"]).grid(
            row=1, column=0, sticky="e", pady=6
        )
        username_entry = tk.Entry(frame, width=28, bg=theme["entry_bg"], fg=theme["entry_fg"],
                                   insertbackground=theme["entry_fg"])
        username_entry.grid(row=1, column=1, pady=6)

        tk.Label(frame, text="Password", bg=theme["bg"], fg=theme["fg"]).grid(
            row=2, column=0, sticky="e", pady=6
        )
        password_entry = tk.Entry(frame, width=28, show="*", bg=theme["entry_bg"],
                                   fg=theme["entry_fg"], insertbackground=theme["entry_fg"])
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
        tk.Button(frame, text="Log in", width=14, command=attempt_login,
                  bg=theme["button_bg"], fg=theme["button_fg"]).grid(
            row=3, column=0, columnspan=2, pady=(16, 4)
        )

        toggle_text = "Switch to Light Mode" if self.dark_mode else "Switch to Dark Mode"
        tk.Button(frame, text=toggle_text, relief="flat", bd=0,
                  bg=theme["bg"], fg=theme["muted"],
                  activebackground=theme["bg"], activeforeground=theme["fg"],
                  command=self.toggle_dark_mode).grid(
            row=4, column=0, columnspan=2, pady=(14, 0)
        )

        font_row = tk.Frame(frame, bg=theme["bg"])
        font_row.grid(row=5, column=0, columnspan=2, pady=(8, 0))
        tk.Label(font_row, text="Text size", bg=theme["bg"], fg=theme["muted"]).pack(side="left")
        tk.Button(font_row, text="A-", width=3, relief="flat",
                  bg=theme["button_bg"], fg=theme["button_fg"],
                  command=self.decrease_font_size).pack(side="left", padx=(8, 2))
        tk.Button(font_row, text="A+", width=3, relief="flat",
                  bg=theme["button_bg"], fg=theme["button_fg"],
                  command=self.increase_font_size).pack(side="left")


    #  Dashboard 

    def show_dashboard(self, preserve_screen=False):
        self.clear()
        theme = self.theme
        root = tk.Frame(self.container, bg=theme["bg"])
        root.pack(fill="both", expand=True)

        sidebar = tk.Frame(root, width=200, bg=theme["panel_bg"])
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, bg=theme["panel_bg"], fg=theme["panel_fg"],
            text=f"{self.current_user.full_name}\n{self.current_user.role}\n"
                 f"{self.current_user.branch_location}",
            justify="left", font=self.font_sidebar, pady=16
        ).pack(fill="x", padx=10)

        self.content = tk.Frame(root, padx=16, pady=16, bg=theme["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        actions = self._menu_for_role(self.current_user.role)
        for label, handler in actions:
            tk.Button(sidebar, text=label, anchor="w", relief="flat",
                      bg=theme["menu_button_bg"], fg=theme["menu_button_fg"],
                      activebackground=theme["menu_button_active_bg"],
                      activeforeground=theme["menu_button_fg"],
                      command=self._nav(handler)).pack(fill="x", padx=10, pady=4)

        tk.Button(sidebar, text="Log out", anchor="w", relief="flat",
                  bg=theme["logout_bg"], fg=theme["logout_fg"],
                  activebackground=theme["logout_bg"], activeforeground=theme["logout_fg"],
                  command=self.show_login).pack(
            fill="x", padx=10, pady=(30, 4)
        )

        toggle_text = "Switch to Light Mode" if self.dark_mode else "Switch to Dark Mode"
        tk.Button(sidebar, text=toggle_text, anchor="w", relief="flat",
                  bg=theme["toggle_bg"], fg=theme["toggle_fg"],
                  activebackground=theme["menu_button_active_bg"],
                  activeforeground=theme["toggle_fg"],
                  command=self.toggle_dark_mode).pack(
            fill="x", padx=10, pady=(4, 10), side="bottom"
        )

        font_row = tk.Frame(sidebar, bg=theme["panel_bg"])
        font_row.pack(fill="x", padx=10, pady=(4, 0), side="bottom")
        tk.Label(font_row, text="Text size", bg=theme["panel_bg"], fg=theme["panel_fg"]).pack(
            side="left"
        )
        tk.Button(font_row, text="A+", width=3, relief="flat",
                  bg=theme["menu_button_bg"], fg=theme["menu_button_fg"],
                  activebackground=theme["menu_button_active_bg"],
                  activeforeground=theme["menu_button_fg"],
                  command=self.increase_font_size).pack(side="right", padx=(2, 0))
        tk.Button(font_row, text="A-", width=3, relief="flat",
                  bg=theme["menu_button_bg"], fg=theme["menu_button_fg"],
                  activebackground=theme["menu_button_active_bg"],
                  activeforeground=theme["menu_button_fg"],
                  command=self.decrease_font_size).pack(side="right")

        if preserve_screen and self.current_screen in dict(actions).values():
            self.current_screen()
        else:
            self.current_screen = actions[0][1]
            self.current_screen()  # show first screen by default

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
        tk.Label(self.content, text="Register tenant", font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text="Tenants", font=self.font_heading).pack(anchor="w")
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
                 font=self.font_heading).pack(anchor="w")
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
                 fg=self.theme["muted"]).pack(anchor="w")

    def screen_log_maintenance(self):
        self.clear_content()
        tk.Label(self.content, text="Log maintenance request",
                 font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text="Apartments", font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text="Generate invoice", font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text="Record payment", font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text="Invoices", font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text="Financial summary", font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text=text, font=self.font_mono, justify="left",
                 pady=20).pack(anchor="w")

    #  Maintenance screens 

    def screen_maintenance_open(self):
        self.clear_content()
        tk.Label(self.content, text="Open / scheduled requests",
                 font=self.font_heading).pack(anchor="w")
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
                 font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text="Manage apartments", font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text="Manage users", font=self.font_heading).pack(anchor="w")
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
        tk.Label(self.content, text="Lease tracking", font=self.font_heading).pack(anchor="w")
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
                 font=self.font_heading).pack(anchor="w")
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
                 font=self.font_heading).pack(anchor="w")
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
                 font=self.font_heading).pack(anchor="w")
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