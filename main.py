import requests
from playwright.sync_api import Playwright, sync_playwright


def generate_format_string(fields):
    parts = []
    for field in fields:
        name, width = field
        if width is None:
            parts.append('{}')
        else:
            parts.append('{:<{}}')
    return ' -- '.join(parts)





def get_station_code():
    """
    @FunctionName：get_station
    @Description：
    @Author：Libre
    @Return:
    @CreateDate: 2023/7/6
    """
    url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js'
    response = requests.get(url)
    js = response.text.replace("var station_names ='", '').replace("';", "")

    result = {}
    for item in js.split('|||'):
        if item:
            parts = item.split('|')
            result[parts[1]] = {'ID': parts[2], '缩写': parts[3]}
    return result


def run(playwright: Playwright) -> None:
    browser_choose = input("请选择你的浏览器\n输入: 1 --> 打开谷歌浏览器\n输入: 2 --> 打开Edge浏览器\n")
    if browser_choose == "1":
        channel = "chrome"
    elif browser_choose == "2":
        channel = "msedge"
    else:
        print("选择无效...")
        return
    browser = playwright.chromium.launch(
        headless=False,
        channel=channel,
        args=['--disable-blink-features=AutomationControlled'])
    # browser.add_init_script(
    #     "() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }) }"
    # )
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://kyfw.12306.cn/otn/resources/login.html')
    if page.url == "https://kyfw.12306.cn/otn/resources/login.html":
        usename = input("请输入你的手机号或12306账号")
        passwd = input("请输入你的密码")
        page.locator('//input[@id="J-userName"]').fill(usename)
        page.locator('//input[@id="J-password"]').fill(passwd)
        page.locator('//a[@id="J-login"]').click()
        # 等待页面跳转
        page.wait_for_timeout(2000)
        # 获取滑块元素
        slider_handle = page.query_selector('//span[@id="nc_1_n1z"]')  # 替换为滑块元素的选择器
        handle_width = slider_handle.bounding_box()['width']
        # 计算滑动距离
        slider_width = page.query_selector('//span[@class="nc-lang-cnt"]').bounding_box()['width']
        print(slider_width)
        slide_distance = slider_width - handle_width

        # 模拟鼠标拖动滑块
        page.mouse.move(slider_handle.bounding_box()['x'] + handle_width / 2,
                        slider_handle.bounding_box()['y'] + handle_width / 2)
        page.mouse.down()
        page.mouse.move(slider_handle.bounding_box()['x'] + handle_width / 2 + slide_distance,
                        slider_handle.bounding_box()['y'] + handle_width / 2)
        page.mouse.up()

    # 到达首页
    page.route("**/*.{png,jpg,jpeg}", lambda route, request: route.abort())
    page.goto('https://www.12306.cn/index/index.html')
    station_list = get_station_code()
    # https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc&fs={},IOQ&ts={},OHH&date=2023-07-06&flag=N,N,Y
    fromStationText = input("请输入出发车站\n")
    fromStation_ID = station_list[fromStationText]['ID']

    toStationText = input("请输入到达车站\n")
    toStation_ID = station_list[toStationText]['ID']

    train_date = input("选择出发日期[例如2023-07-06]\n")

    page.goto(f'https://kyfw.12306.cn/otn/leftTicket/init?linktypeid=dc&fs={fromStationText},{fromStation_ID}'
              f'&ts={toStationText},{toStation_ID}&date={train_date}&flag=N,N,Y')

    # page.locator('//li[@id="isHighDan"]').click()
    # # page.evaluate("document.querySelector('#train_date').blur()")

    table_list = page.query_selector_all(
        f'//tr[starts-with(@id, "ticket") and .//a[text()="预订"] and .//strong[text() = "{fromStationText}"]]'
        f' and .//strong[text() = "{toStationText}"]]'
    )
    # //td[@class="no-br" and text()="预订"]
    for table in table_list:
        # if fromStation_ID not in station_Name:
        #     continue

        station_number = table.query_selector('//a[@class="number"]').text_content()

        start_station = table.query_selector_all('//div[@class="cdz"]/strong')[0].text_content()

        end_station = table.query_selector_all('//div[@class="cdz"]/strong')[1].text_content()

        start_time = table.query_selector_all('//div[@class="cds"]/strong')[0].text_content()

        end_time = table.query_selector_all('//div[@class="cds"]/strong')[1].text_content()

        elements = table.query_selector_all('//td')[1:-1]
        station_Data = [station_number, start_station, end_station, start_time, end_time]
        price_list = []
        for element in elements:
            aria_label = element.get_attribute('aria-label')
            if aria_label is None or "余票候补" in aria_label.split('，') or "余票无" in aria_label.split('，'):
                continue
            station_Data.append(f"{aria_label.split('，')[1]}, {aria_label.split('，')[2]}")
            price_list.append(f"{aria_label.split('，')[1]}, {aria_label.split('，')[2]}")
        format_string = "{:^6}  --  {:^6}  --  {:^6}  --  {:^6}  --  {:^6}  "
        format_string += ''.join(['--  {:^18}  ' for _ in range(len(price_list))])
        format_string = format_string[:-2]
        output = format_string.format(*station_Data)
        print(output)
    input("x")
    #  //tr[starts-with(@id, "ticket")]


with sync_playwright() as playwright:
    run(playwright)
