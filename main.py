import os
import asyncio
import argparse

from pyppeteer import launch


UserAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) " \
            "AppleWebKit/537.36 (KHTML, like Gecko) " \
            "Chrome/78.0.3904.97 Safari/537.36"


async def create_wiki(page, create_wiki_url, title, content, parent_name="", remarks=""):
    await page.goto(create_wiki_url)
    await asyncio.sleep(3)
    await page.focus('#WikiName')
    await page.keyboard.type(title)
    await page.focus('#input')
    await page.keyboard.type(content)
    # 回滚到页面底部
    await page.evaluate('window.scrollBy(0, document.body.scrollHeight)')
    await page.focus('#WikiNote')
    await page.keyboard.type(remarks)
    if parent_name:
        await page.focus('#Markdown_wikiParentName')
        await page.keyboard.type(parent_name)
    await page.click('#wiki_btn_submit')
    await asyncio.sleep(1)


async def main(params):
    browser = await launch(headless=True)
    await browser.newPage()
    page = await browser.newPage()
    await page.setUserAgent(UserAgent)
    # 登录开始
    await page.goto('https://www.tapd.cn/cloud_logins/login')
    await page.focus('#username')
    await page.keyboard.type(params.username)
    await page.focus('#password_input')
    await page.keyboard.type(params.password)
    await page.click('#tcloud_login_button')
    # TODO：登录用户名和密码有误的处理
    # TODO：登录是否成功的验证
    # 登录结束
    await asyncio.sleep(3)
    # 进入 wiki 页面
    wiki_url = await page.querySelectorEval('#myprojects-list > li:nth-child(2) > a', '(e => e.href)')
    create_wiki_url = f"{wiki_url.split('?')[0]}wikis/add?parent_wiki="
    # 批量创建 wiki
    for p in params.import_list:
        with open(p, "rb") as f:
            title = f"{os.path.dirname(p).rstrip('/')}_{os.path.basename(p)}"
            await create_wiki(page, create_wiki_url,
                              title=title,
                              content=f.read())
    await asyncio.sleep(3)
    await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import Wiki to Tapd.')
    parser.add_argument('--username', metavar='u', type=str, required=True,
                        help='username for tapd')
    parser.add_argument('--password', metavar='p', type=str, required=True,
                        help='password for tapd')
    parser.add_argument('--folder', metavar='F', type=str,
                        help='folder path of import files')
    parser.add_argument('--file', metavar='f', type=str,
                        help='file path of import files')
    params = parser.parse_args()
    import_list = []
    if "folder" in params:
        if not os.path.isdir(params.folder):
            raise Exception(f"{params.folder} is not directory.")
        for filename in os.listdir(params.folder):
            if filename.endswith(".md") or filename.endswith(".markdown"):
                import_list.append(os.path.join(params.folder, filename))
    elif "file" in params:
        if not os.path.isfile(params.file):
            raise Exception(f"{params.file} is not file.")
        if params.file.endswith(".md") or params.file.endswith(".markdown"):
            import_list.append(params.file)
    else:
        raise Exception("Select at least one for file and folder.")
    if not import_list:
        raise Exception("Empty.")
    setattr(params, "import_list", import_list)
    asyncio.get_event_loop().run_until_complete(main(params))
