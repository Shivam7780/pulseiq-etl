# PulseIQ Dashboard Design Notes

## Dashboard
Headcount & Departments

## 1. Design approach
Use a clean workforce analytics dashboard with a clear hierarchy, readable
labels, accessible colors, and enough spacing for laptop and mobile screens.

The AI-generated mockup was used for layout ideas only. Its example KPI values,
chart values, and takeaway sentences are illustrative and must not be used as
actual business results.

## 2. Layout
- Header: dashboard title and reporting period.
- Top row: four KPI cards for current headcount, monthly hires, monthly exits,
  and department count.
- Main row: headcount trend and department split.
- Lower row: tenure bands, role mix, and joiners-versus-leavers trend.
- Side filter area: department and date range.
- Each chart includes a short takeaway sentence directly underneath it.

## 3. Visual and accessibility rules
- Use a color-blind-safe palette; do not rely on color alone to communicate meaning.
- Use consistent typography and readable chart labels.
- Use clear chart titles matching the official metric dictionary where applicable.
- Format headcount, hires, exits, and department totals as whole numbers.
- Format dates consistently as Month YYYY.
- Use a consistent, readable number format for percentages if added later.
- Keep sufficient contrast between text and backgrounds.
- Avoid overcrowding; allow charts to stack vertically on narrow screens.
- Show aggregated workforce data only and respect minimum group-size rules.

## 4. Data and metric definitions
- Headcount: active employees on the last day of the month.
- Hires: employees whose hire date falls in the month; transfers are not hires.
- Exits: employees whose exit date falls in the month.
- Use the warehouse schema `dw` as the dashboard data source.
- Use the employee history key correctly so historical department assignments
  are not replaced by an employee's current department.
- Use actual warehouse query results for every KPI and chart takeaway.

## 5. Design review and improvements
- Put the most important workforce number first in the KPI row.
- Keep the department and date filters easy to find.
- Use consistent spacing, chart titles, and number formats.
- Replace illustrative mockup numbers with verified warehouse results.
- Check the dashboard at laptop width and a narrow/mobile width.
- Check color contrast and verify that labels remain understandable without color.
- Ensure every chart has a concise, data-supported takeaway sentence.

## 6. Validation status
Initial layout and style rules documented.
Warehouse-backed KPI values, chart results, and takeaways still require validation.
Superset connection and dashboard export remain to be completed.
