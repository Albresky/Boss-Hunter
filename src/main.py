# main.py

from patchright.sync_api import sync_playwright
from job_scraper import JobScraper
from login_manager import LoginManager
from data_manager import DataManager
from datetime import datetime

from config import logger, BOSS_BASE_URL


def main():
    with sync_playwright() as p:
        # 使用内置的 chromium
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(base_url=BOSS_BASE_URL)
        page = context.new_page()

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"boss直聘_感兴趣职位_{timestamp}.csv"
            data_manager = DataManager(filename)

            # 1. 登录
            login_manager = LoginManager(page)
            login_manager.login()

            # 2. 爬取感兴趣的职位
            scraper = JobScraper(page, data_manager)
            count_job_data = scraper.scrape_interested_jobs()

            # 3. (下一步) 处理数据和保存
            if count_job_data > 0:
                data_manager.convert_csv_to_json()
                data_manager.update_master_file()
                logger.info(
                    f"成功提取 {count_job_data} 条感兴趣的职位数据，已保存到 {filename}"
                )
            logger.info("\n所有流程完成。")

            input("按 Enter 键关闭浏览器...")

        except Exception as e:
            logger.info(f"发生错误: {e}")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
