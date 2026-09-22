# Power BI page integration

The public UrbanIQ website now has a live embedded Power BI report at `/powerbi`.
The supplied report-page exports are still retained in this folder and under `frontend/public/powerbi-pages/`; the application exposes each as a collapsible archived reference below the live report, alongside its chart interpretation. `Main page.png` remains a README portfolio image and is intentionally not used as an application page.

## Page and chart purpose

### Ward Overview (`first.png`)

- **Total complaints**: headline volume of the currently loaded complaint records.
- **Average resolution days**: average latest ward-level resolution time; a quick service-speed indicator.
- **Resolved complaints**: count of portal records currently marked resolved.
- **Resolution rate**: resolved records divided by total records.
- **Complaint distribution by category**: donut chart showing which civic issues dominate the selected scope.
- **Total complaints by ward**: compares complaint volume across wards and highlights where demand is concentrated.
- **Ward resolution rate**: compares the share of complaints resolved for each ward.

### Complaint Intelligence (`second.png`)

Uses the same operational measures as Ward Overview, with ward and category filters intended for comparison and investigation. The category donut and the two ward bar charts update with the selected filters.

### Civic Performance (`third.png`)

- **Civic engagement vs ward health**: scatter plot where the x-axis is per-capita deliberations, the y-axis is the computed health score, and bubble size represents complaint volume. It helps identify wards with strong civic participation but weak outcomes, or weak participation and weak outcomes.
- **Ward health scores**: ranked comparison of the computed 0-100 health score.
- **Average resolution days**: service-speed comparison by ward.

### Complaint Investigation (`fourth.png`)

- **Investigation flow counters**: show the filtered record count, number of wards, and number of categories in scope.
- **Complaint table**: exposes complaint ID, ward, category, status, and creation date for the first 50 filtered records. This is the operational drill-through surface.

### Ward Details (`fifth.png`)

- **Ward health score**: selected ward's computed health score and label.
- **Total complaints**: latest civic-metrics complaint volume for that ward.
- **Resolution rate**: closed latest-metrics complaints divided by total complaints.
- **Average resolution**: latest average resolution time in days.
- **Complaints by status**: donut showing open, in-progress, and resolved portal complaints.
- **Complaints by category**: bar chart identifying the selected ward's issue mix.

## Data sources

The page uses existing public Django endpoints:

- `/api/health-scores/`
- `/api/councillors/`
- `/api/complaints/?page_size=500`

The Power BI screenshots remain stored in this folder for visual reference. The React implementation is intentionally live-data driven, so it reflects UrbanIQ's current backend rather than hard-coded screenshot values.
