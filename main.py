#coding=utf-8                                                                                                                                                                              
import io, base64
import pdf2image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.print_page_options import PrintOptions

# Take screenshot of page
def screenshot_page():
    # Show whole page
    S = lambda X: driver.execute_script('return document.body.parentNode.scroll'+X)
    driver.set_window_size(S('Width'),S('Height'))

    # Screenshot all webpage                                                                             
    # driver.find_element(by=By.TAG_NAME, value='body').screenshot('web_screenshot.png')
    # Screenshot only guide text
    driver.find_element(by=By.CLASS_NAME, value='ffaqbody').screenshot('web_screenshot.png')

# Print page into PDF, then convert that to PNG
def print_page():
    # Set page options
    print_options = PrintOptions()
    # Set ratio of paper to 16:9
    print_options.page_width = 16
    print_options.page_height = 9

    # Add comfortable margins
    print_options.margin_top = 0.5
    print_options.margin_bottom = 0.5
    print_options.margin_left = 0.5
    print_options.margin_right = 0.5

    # Convert page into base64 encoded PDF script
    pdf_base64 = driver.print_page(print_options)
    pdf_bytes = base64.b64decode(pdf_base64)
    
    # Convert PDF into PNG files
    pdf2image.convert_from_bytes(pdf_bytes, output_folder="img", fmt="png", poppler_path="bin", size=(960,544))

    # with open('print.pdf', 'wb') as file:
    #     file.write(pdf_bytes)

options = webdriver.EdgeOptions()
options.headless = True
options.add_argument('window-size=960x544')
driver = webdriver.Edge(options=options)

url = sys.argv[1]
driver.get(url)
# driver.get("data:text/html;charset=utf-8," + html_content)

# Remove scrollbar
#driver.execute_script('document.styleSheets[0].insertRule("body {overflow: hidden;}", 0 )')

# Remove cookie overlay
# Remove by removing element
driver.execute_script("document.getElementById('onetrust-consent-sdk').remove();")
# Remove by clicking accept button (doesn't work)
#driver.find_element(by=By.XPATH, value='//*[@id="onetrust-accept-btn-handler"]').click()

# screenshot_page()
print_page()

driver.quit()