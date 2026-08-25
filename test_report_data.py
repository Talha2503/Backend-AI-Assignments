import json

from report_data import getReportData


report = getReportData()

print(json.dumps(report, indent=2))