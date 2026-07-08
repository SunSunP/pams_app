# Manual GUI test checklist (for screenshot evidence)

The automated suite in this folder (`test_validators.py`, `test_models.py`,
`test_security.py`, `test_repositories.py`) covers the logic layer directly.
Your coursework also asks for screenshot evidence of bad data being rejected
*through the running application*, since that's what a marker can see at a
glance. Run `python3 main.py` and walk through the cases below, taking a
screenshot of each result (the error dialog, or the success dialog) for your
report's "Actual output" column.

| # | Screen | Role to log in as | Input | Expected result |
|---|--------|-------------------|-------|------------------|
| 1 | Register tenant | fdesk.bristol | NI number: `"INVALID"` | Error dialog: invalid NI number, no record created |
| 2 | Register tenant | fdesk.bristol | Email: `"not-an-email"` | Error dialog: invalid email |
| 3 | Register tenant | fdesk.bristol | All fields valid | Success dialog with new tenant ID |
| 4 | Assign apartment / lease | fdesk.bristol | End date before start date | Error dialog: end_date must be after start_date |
| 5 | Assign apartment / lease | fdesk.bristol | Student tenant, lease spanning 4 years (undergrad max is 2) | Error dialog: lease duration exceeds maximum allowed |
| 6 | Manage apartments | admin.bristol | Monthly rent: `-100` | Error dialog: monthly_rent must be greater than zero |
| 7 | Manage apartments | admin.bristol | Number of rooms: `0` | Error dialog: num_rooms must be greater than zero |
| 8 | Resolve maintenance request | maint.manchester | Total cost: `-50` | Error dialog: total_cost cannot be negative |
| 9 | Record payment | finance.london | Amount less than invoice total | Error dialog: payment amount is less than invoice amount |
| 10 | Manage users | fdesk.bristol (try to navigate here — button won't even appear) | n/a | Confirms RBAC hides the screen entirely for unauthorised roles |
| 11 | Login | any | Wrong password for a valid username | Error dialog: invalid username or password |
| 12 | Terminate lease early | admin.bristol | Valid lease, termination date within the next 30 days | Success dialog showing penalty **and** a "less than 1 month notice" warning |

After completing the checklist, paste each screenshot into your report next
to the matching automated test from `test_run_output.txt`, so each business
rule has both an automated proof and a visual one.
