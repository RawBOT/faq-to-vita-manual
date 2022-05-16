#coding=utf-8                                                                                                                                                                              
import io, os, sys, pathlib
from optparse import OptionParser, OptionGroup
import base64, urllib.request, zipfile
import pdf2image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.print_page_options import PrintOptions

thirdparty_dir = pathlib.Path("3rdparty")

# Downloads required binaries
def download_reqs():
    thirdparty_dir.mkdir(parents=True, exist_ok=True)

    # Download and extract Poppler
    path = pathlib.Path(thirdparty_dir / "poppler-22.04.0")
    if not path.exists():
        path.mkdir(parents=True)
        url = 'https://github.com/oschwartz10612/poppler-windows/releases/download/v22.04.0-0/Release-22.04.0-0.zip'
        filehandle, _ = urllib.request.urlretrieve(url)
        with zipfile.ZipFile(filehandle, 'r') as zip:
            # binary_files = [ file for file in zip.namelist() if file.startswith(str((path / "Library/bin/").relative_to(thirdparty_dir)).replace(os.sep, os.altsep)) ]
            for file in zip.namelist():
                if file.startswith(str((path / "Library/bin/").relative_to(thirdparty_dir)).replace(os.sep, os.altsep)):
                    zip.extract(file, thirdparty_dir)

        # Download license file
        url = "https://raw.githubusercontent.com/oschwartz10612/poppler-windows/v22.04.0-0/LICENSE"
        filehandle, _ = urllib.request.urlretrieve(url, str(path / "LICENSE"))

    # Download browser drivers
    path = pathlib.Path(thirdparty_dir / "browser_drivers")
    if not path.exists():
        path.mkdir(parents=True)
        # Edge
        url = "https://msedgedriver.azureedge.net/101.0.1210.47/edgedriver_win64.zip"
        filehandle, _ = urllib.request.urlretrieve(url)
        with zipfile.ZipFile(filehandle, 'r') as zip:
            zip.extract("msedgedriver.exe", str(path))

        # Firefox
        # url = "https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-win64.zip"
        # filehandle, _ = urllib.request.urlretrieve(url)
        # with zipfile.ZipFile(filehandle, 'r') as zip:
        #     zip.extract("geckodriver.exe", str(path))

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
    output_dir = parser_options.output_dir
    pathlib.Path(output_dir).mkdir(exist_ok=True)
    pdf2image.convert_from_bytes(pdf_bytes, output_folder=output_dir, fmt="png", poppler_path=thirdparty_dir / "poppler-22.04.0/Library/bin", size=(960,544))

    # with open('print.pdf', 'wb') as file:
    #     file.write(pdf_bytes)

def setup_parser():
    parser = OptionParser(usage="%prog [OPTIONS] URL", version="%prog 1.2")
    parser.set_description("Converts an online guide into PNG files to be used as a Vita manual.")
    parser.add_option("-o", "--outputdir", dest="output",
                      help="Output images to DIR", metavar="DIR")

    parser.set_defaults(output_dir="output/", verbose=False)

    return parser

# Download required binaries
download_reqs()

parser = setup_parser()
(parser_options, args) = parser.parse_args()

options = webdriver.EdgeOptions()
options.headless = True

options.add_argument('window-size=960x544')
driver = webdriver.Edge(thirdparty_dir / r"browser_drivers/msedgedriver.exe", options=options)

url = args[0]
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