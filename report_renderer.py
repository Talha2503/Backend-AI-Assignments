from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright


def build_html(report_data):
    today = date.today().strftime("%B %d, %Y")

    summary = report_data["summary"]
    top_products = report_data["top_products"]
    orders_per_day = report_data["orders_per_day"]

    top_products_rows = "".join(
        f"""
        <tr>
            <td>{product["product"]}</td>
            <td>${product["revenue"]:,.2f}</td>
        </tr>
        """
        for product in top_products
    )

    orders_rows = "".join(
        f"""
        <tr>
            <td>{order["date"]}</td>
            <td>{order["orders"]}</td>
        </tr>
        """
        for order in orders_per_day
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Sales Report</title>

        <style>
            @page {{
                size: A4;
                margin: 20mm;
            }}

            body {{
                font-family: Arial, sans-serif;
                color: #222;
                margin: 0;
            }}

            h1 {{
                margin-bottom: 5px;
            }}

            .date {{
                color: #666;
                margin-bottom: 25px;
            }}

            .summary {{
                display: flex;
                gap: 20px;
                margin-bottom: 30px;
            }}

            .card {{
                border: 1px solid #ddd;
                padding: 15px;
                flex: 1;
                border-radius: 6px;
            }}

            .card-title {{
                font-size: 12px;
                color: #666;
                margin-bottom: 5px;
            }}

            .card-value {{
                font-size: 22px;
                font-weight: bold;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}

            th,
            td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}

            th {{
                background: #f2f2f2;
            }}

            thead {{
                display: table-header-group;
            }}

            tr {{
                break-inside: avoid;
                page-break-inside: avoid;
            }}

            h2 {{
                margin-top: 25px;
            }}
        </style>
    </head>

    <body>
        <h1>Sales Report</h1>
        <div class="date">Generated on {today}</div>

        <div class="summary">
            <div class="card">
                <div class="card-title">Total Orders</div>
                <div class="card-value">
                    {summary["total_orders"]}
                </div>
            </div>

            <div class="card">
                <div class="card-title">Total Revenue</div>
                <div class="card-value">
                    ${summary["total_revenue"]:,.2f}
                </div>
            </div>

            <div class="card">
                <div class="card-title">Average Order</div>
                <div class="card-value">
                    ${summary["average_order_amount"]:,.2f}
                </div>
            </div>
        </div>

        <h2>Top 5 Products by Revenue</h2>

        <table>
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Revenue</th>
                </tr>
            </thead>
            <tbody>
                {top_products_rows}
            </tbody>
        </table>

        <h2>Orders Per Day — Last 7 Days</h2>

        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Orders</th>
                </tr>
            </thead>
            <tbody>
                {orders_rows}
            </tbody>
        </table>
    </body>
    </html>
    """


def generate_pdf(report_data, output_path="reports/test.pdf"):
    html = build_html(report_data)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        page.set_content(html, wait_until="networkidle")

        page.pdf(
            path=str(output),
            format="A4",
            print_background=True,
        )

        browser.close()

    return output