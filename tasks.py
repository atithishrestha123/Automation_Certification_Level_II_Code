from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

import shutil
import os

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates a ZIP archive of the receipts and images.
    """
    open_robot_order_website()

    orders = get_orders()

    for order in orders:
        handle_modal_if_present()

        process_order(order)

        order_number = order['Order number']
        pdf_path = save_receipt_as_pdf(order_number)
        screenshot_path = capture_robot_screenshot(order_number)
        add_screenshot_to_pdf(screenshot_path, pdf_path)

        prepare_next_order()
    
    create_zip_archive_of_receipts()

def open_robot_order_website():
    """Navigates to the robot order URL."""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def get_orders():
    """Downloads the orders CSV file and returns it as a list of dictionaries."""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    
    tables = Tables()
    data = tables.read_table_from_csv("orders.csv", header=True)
    return data

def handle_modal_if_present():
    """Handles the initial alert if it appears."""
    page = browser.page()
    if page.locator('.alert-buttons > button:nth-child(1)').is_visible():
        page.click('.alert-buttons > button:nth-child(1)')

def process_order(order):
    """Fills out the robot order form and resubmits if submission fails."""
    while True:
        fill_order_form(order)
        if is_submission_successful():
            break

def fill_order_form(order):
    """Fills the form with the given order details."""
    page = browser.page()
    page.select_option("#head", str(order["Head"]))
    page.click(f"#id-body-{order['Body']}")
    page.fill('//*[@class="form-control"][1]', str(order['Legs']))
    page.fill("#address", order["Address"])
    page.click("#order")

def prepare_next_order():
    """Clicks the 'Order Another' button to prepare the next order."""
    page = browser.page()
    page.click("#order-another")

def save_receipt_as_pdf(order_number):
    """Saves the receipt as a PDF file."""
    page = browser.page()
    receipt_html = page.locator("#receipt").inner_html()

    pdf = PDF()
    pdf_filename = f"output/receipts/{order_number}.pdf"
    pdf.html_to_pdf(receipt_html, pdf_filename)
    return pdf_filename

def capture_robot_screenshot(order_number):
    """Captures a screenshot of the ordered robot."""
    page = browser.page()
    screenshot_filename = f"output/receipts_screenshots/{order_number}.png"

    robot_preview_element = page.locator("#robot-preview-image")
    robot_preview_element.screenshot(path=screenshot_filename)
    
    return screenshot_filename

def add_screenshot_to_pdf(screenshot, pdf_file):
    """Embeds the screenshot into the PDF receipt."""
    pdf = PDF()
    pdf.add_watermark_image_to_pdf(
        image_path=screenshot,
        source_path=pdf_file,
        output_path=pdf_file,
    )

def is_submission_successful():
    """Returns True if the form submission was successful, False otherwise."""
    page = browser.page()
    return not (page.locator('.alert-danger').is_visible())

def create_zip_archive_of_receipts():
    """Creates a ZIP archive of the receipt PDFs."""
    shutil.make_archive('output/receipts', 'zip', 'output/receipts')