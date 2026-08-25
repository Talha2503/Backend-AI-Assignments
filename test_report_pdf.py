from report_data import getReportData
from report_renderer import generate_pdf


report = getReportData()

output = generate_pdf(report)

print(f"PDF generated successfully: {output}")