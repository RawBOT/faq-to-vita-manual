#coding=utf-8                                                                                                                                                                              
import io, os, sys, pathlib
import shutil, tempfile
from optparse import OptionParser, OptionGroup
import base64, urllib.request, zipfile
import pdf2image
import requests
import urllib.parse
from bs4 import BeautifulSoup
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
            # binary_files = [ file for file in zip.namelist() if file.startswith(str((path / "Library/bin/")
            #                .relative_to(thirdparty_dir)).replace(os.sep, os.altsep)) ]
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
    global driver, parser_options
    # Set page options
    print_options = PrintOptions()
    # Set ratio of paper to 16:9
    if parser_options.paper_size == "small":
        print_options.page_width = 19.5
        print_options.page_height = 11.05
    elif parser_options.paper_size == "large":
        print_options.page_width = 12
        print_options.page_height = 6.8
    # elif parser_options.paper_size == "medium":
    else:
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
    output_dir = pathlib.Path(parser_options.output_dir)
    temp_dir = output_dir / "temp"
    pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)
    output_files = pdf2image.convert_from_bytes(pdf_bytes, output_folder=temp_dir, fmt="png", output_file="out_",  
                                                poppler_path=thirdparty_dir / "poppler-22.04.0/Library/bin", 
                                                size=(960,544), dpi=600, paths_only=True)

    # Rename output files to Vita manual format, e.g. 001.png, 002.png, etc.
    counter = 1
    for filepath in output_files:
        shutil.move(filepath, output_dir / "{0:03d}.png".format(counter))
        counter = counter + 1

    # with open('print.pdf', 'wb') as file:
    #     file.write(pdf_bytes)

def setup_parser():
    parser = OptionParser(usage="%prog [OPTIONS] URL", version="%prog 1.2")
    parser.set_description("Converts an online guide into PNG files to be used as a Vita manual.")
    parser.add_option("-s", "--size", dest="paper_size", default="medium",
                      help="Size of text: small, medium or large. Maximum number of pages allowed"
                      "is 999, any more and the Vita manual option will crash [default: %default]")
    parser.add_option("-o", "--outputdir", dest="output",
                      help="Output images to DIR", metavar="DIR")

    parser.set_defaults(output_dir="output/", verbose=False)

    return parser

# Global vars
driver = None
parser_options = None

if __name__ == "__main__":
    # Download required binaries
    download_reqs()

    parser = setup_parser()
    (parser_options, args) = parser.parse_args()

    url = args[0]

    parsed_url = urllib.parse.urlparse(url)
    guide_id = os.path.basename(parsed_url.path)

    # Add query parameter "single=1" to URL if not there to produce a single page guide
    if "single=1" not in url:
        parsed_query = urllib.parse.parse_qs(parsed_url.query)
        if "single" not in parsed_query:
            parsed_query['single'] = ['1']
        else:
            if '1' not in parsed_query['single']:
                parsed_query['single'] = ['1']
        new_query = urllib.parse.urlencode(parsed_query, doseq=1)
        url = urllib.parse.urlunparse([new_query if i == 4 else x for i,x in enumerate(parsed_url)])

    session = requests.Session()
    response = session.get(url, headers={"user-agent": "Mozilla/5.0 (iPad; U; CPU OS 3_2_1 like Mac OS X;" \
                                        "en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Mobile/7B405"})
    soup = BeautifulSoup(response.text, features="html5lib")

    faq_body = soup.find('div', id="faqwrap")
    # Fix images when ?single=1 is used
    for img_tag in faq_body.find_all('img'):
        # Convert from format e.g. '/ffaq/3/202/' to e.g. /a/faqs/79/76979-202.jpg
        img_tag.attrs['src'] = 'https://' + parsed_url.hostname + '/a/faqs/' + guide_id[3:] + '/' + guide_id \
                           + '-' + os.path.basename(img_tag.attrs['src'][:-1]) + '.jpg'

        img_tag.attrs['width'] = "auto"
        img_tag.attrs['height'] = "260%"

    html_content = str(faq_body).replace("#", "")  # remove # character, since it breaks parsing

    options = webdriver.EdgeOptions()
    options.headless = True
    options.add_argument('window-size=960x544')

    driver = webdriver.Edge(thirdparty_dir / r"browser_drivers/msedgedriver.exe", options=options)

    with tempfile.NamedTemporaryFile('w', encoding="utf-8", suffix=".html", delete=False) as temp_html_file:
        temp_html_file.write(html_content)
        temp_html_file.flush()

    local_url = "file:///" + temp_html_file.name
    driver.get(local_url)
    print_page()

    os.remove(temp_html_file.name)

    driver.quit()
