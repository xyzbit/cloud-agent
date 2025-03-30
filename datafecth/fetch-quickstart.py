from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def test():
    # 使用 Homebrew 安装的 chromedriver 路径
    chromedriver_path = "/usr/local/bin/chromedriver"
    # '--verbose',  log_output=sys.stdout,
    service = Service(executable_path=chromedriver_path,
                      service_args=['--headless=new','--no-sandbox',
                                    '--disable-dev-shm-usage',
                                    '--disable-gpu',
                                    '--ignore-certificate-errors',
                                    '--ignore-ssl-errors',
                                   ])

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')

    driver = webdriver.Chrome(options=options,service=service)

    driver.get("https://modelscope.cn/my/overview")
    print(driver.title)

    driver.quit()


if __name__ == "__main__":
    test()