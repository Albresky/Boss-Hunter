# job_scraper.py

from datetime import datetime
from patchright.sync_api import Page, expect
import time

from data_manager import DataManager
from config import logger, INTERESTING_JOBS_URL


class JobScraper:
    """
    负责爬取职位信息的类
    """

    def __init__(self, page: Page, data_manager: DataManager):
        self.page = page
        self.interested_url = INTERESTING_JOBS_URL
        self.data_manager = data_manager

    def _extract_job_details(self, job_page: Page) -> dict:
        """
        从职位详情页提取指定的9项信息 (已根据您提供的HTML更新)。
        """
        logger.info("开始提取页面信息...")
        job_data = {}
        try:
            # 等待页面主要信息区域加载
            # job_page.locator("div.info-primary")

            # 定位包含职位、薪资、地点等信息的核心容器
            primary_info = job_page.locator("div.info-primary")

            # 1. 职位名称
            job_data["职位名称"] = primary_info.locator("h1").text_content().strip()

            # 2. 薪资
            job_data["薪资"] = (
                primary_info.locator("span.salary").text_content().strip()
            )

            # 3. 公司
            try:
                # 方案一：常规提取
                job_data["公司"] = (
                    job_page.locator(".company-info-box .company-name")
                    .text_content()
                    .strip()
                )
            except:
                try:
                    # 方案二：从HR信息中提取
                    boss_info_text = (
                        job_page.locator(".boss-info-attr").text_content().strip()
                    )
                    job_data["公司"] = boss_info_text.split("·")[0].strip()
                except:
                    job_data["公司"] = "N/A"

            # 4. base地点
            job_data["base地点"] = (
                primary_info.locator("p a.text-city").text_content().strip()
            )

            # 5. 工作经验 (注意class名可能是experiece)
            try:
                job_data["工作经验"] = (
                    primary_info.locator("p span.text-experiece").text_content().strip()
                )
            except:
                job_data["工作经验"] = (
                    primary_info.locator("p span.text-experience")
                    .text_content()
                    .strip()
                )

            # 6. 学历
            job_data["学历"] = (
                primary_info.locator("p span.text-degree").text_content().strip()
            )

            # 7. 福利待遇 (使用新的父级容器)
            welfare_tags = job_page.locator(
                ".job-banner .tag-container-new .tag-all.job-tags span"
            ).all_text_contents()
            job_data["福利待遇"] = (
                ", ".join(tag.strip() for tag in welfare_tags)
                if welfare_tags
                else "N/A"
            )

            # 8. 职位描述内容 (职位亮点 + 具体描述)
            # 9. 领域tag (职位亮点)
            highlights_tags = job_page.locator(
                "ul.job-keyword-list li"
            ).all_text_contents()

            job_data["领域tag"] = (
                ", ".join(highlights_tags) if highlights_tags else "N/A"
            )

            # job_detail_section = job_page.locator(
            #     ".job-detail > .job-detail-section"
            # ).first
            job_detail_section = job_page.locator(
                ".job-detail-section:has(h3:text('职位描述'))"
            )

            # 10. 具体工作描述jd
            # description_text = (
            #     job_detail_section.locator(".job-sec-text").text_content().strip()
            # )
            import re

            description_html = job_detail_section.locator(
                ".job-sec-text"
            ).first.inner_html()
            description_text = re.sub(
                r"<br\s*/?>", "\r\n", description_html, flags=re.IGNORECASE
            )

            # 移除替换后可能剩余的其他HTML标签（为了代码健壮性）
            description_text = re.sub(r"<[^>]+>", "", description_text)

            # 解码可能存在的HTML实体 (例如 &amp; -> &)
            import html

            job_data["职位描述内容"] = html.unescape(description_text).strip()

            # --- 生成超链接和更新职位描述 ---
            job_url = job_page.url
            # 清理link_text中的双引号，防止破坏Excel公式
            link_text = f"{job_data['职位名称']}-{job_data['base地点']}-{job_data['公司']}".replace(
                '"', '""'
            )
            hyperlink_formula = f'=HYPERLINK("{job_url}", "{link_text}")'

            # 单独添加一列原始链接，方便其他程序处理
            job_data["JD链接"] = hyperlink_formula

            job_data["bossURL"] = job_url.split("?")[0]  # 去除查询参数部分

            job_data["获取时间"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            logger.info(
                f"\n\n====成功提取职位: 【{job_data['职位名称']} - {job_data['公司']} - {job_data['base地点']} - {job_data['薪资']}】====\n\n"
            )
            return job_data

        except Exception as e:
            logger.info(f"提取信息时出错: {e}")
            return None

    def scrape_interested_jobs(self):
        """
        打开“感兴趣”页面，使用正确的选择器自动翻页遍历所有JD，提取信息并返回
        """
        logger.info("\n--- 开始爬取“感兴趣”的职位 ---")
        self.page.goto(self.interested_url)
        logger.info(f"已打开页面: {self.page.url}")

        count_job_data = 0
        page_number = 1

        while True:
            logger.info(f"\n--- 正在处理第 {page_number} 页 ---")
            # 等待职位列表加载完成
            self.page.wait_for_selector("ul.user-jobs-ul", timeout=30000)
            time.sleep(2)  # 增加延时以确保JS渲染完成

            # **【修正】使用您提供的HTML结构来定位职位链接**
            # 1. 定位包含所有职位信息的 li 列表
            job_list_items = self.page.locator("ul.user-jobs-ul li.item-boss").all()
            logger.info(f"当前页面找到了 {len(job_list_items)} 个职位。")

            if not job_list_items:
                logger.info("当前页面没有找到职位，爬取结束。")
                break

            # 提取当前页所有链接，之后再统一访问，避免在循环中操作页面导致元素失效
            urls_to_visit = []
            for item in job_list_items:
                # 2. 在每个 li 内部找到职位详情的 a 标签
                link_element = item.locator("div.job-name a.name")
                href = link_element.get_attribute("href")
                if href:
                    urls_to_visit.append(href)

            # 逐个访问详情页
            for i, job_url in enumerate(urls_to_visit):
                # Playwright的base_url会自动处理拼接
                logger.info(f"正在访问第 {i+1}/{len(urls_to_visit)} 个职位: {job_url}")
                job_page = self.page.context.new_page()
                try:
                    job_page.goto(job_url)
                    job_page.wait_for_load_state("domcontentloaded")
                    job_details = self._extract_job_details(job_page)
                    if job_details:
                        self.data_manager.append_to_csv(job_details)
                        count_job_data += 1
                except Exception as e:
                    logger.info(f"访问或处理页面 {job_url} 时出错: {e}")
                finally:
                    # 确保页面被关闭
                    job_page.close()
                time.sleep(1)  # 礼貌性延时，防止请求过快

            # 【分页逻辑】
            next_page_button = self.page.locator(
                "div.pagination-area i.ui-icon-arrow-right"
            ).locator(
                ".."
            )  # 定位图标，然后返回其父级 a 标签

            # 检查按钮是否存在
            if not next_page_button.is_visible():
                logger.info("未找到“下一页”按钮，爬取结束。")
                break

            # 检查按钮是否被禁用
            class_attr = next_page_button.get_attribute("class") or ""
            if "disabled" in class_attr:
                logger.info("“下一页”按钮已禁用，已到达最后一页。")
                break
            else:
                logger.info("点击“下一页”...")
                next_page_button.click()
                page_number += 1

        logger.info(f"\n--- 所有页面访问完毕，共提取 {count_job_data} 条数据 ---")
        return count_job_data
