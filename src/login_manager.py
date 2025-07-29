# login_manager.py

import time
import json, os

from patchright.sync_api import Page, expect
from config import (
    logger,
    BOSS_BASE_URL,
    BOSS_LOGIN_URL,
    BOSS_RECOMMEND_URL,
    BOSS_SECURITY_CHECK_URL,
)


class LoginManager:
    """
    处理BOSS直聘网站登录的类
    """

    def __init__(self, page: Page):
        """
        初始化 LoginManager
        :param page: Playwright 的 Page 对象
        """
        self.page = page
        self.base_url = BOSS_BASE_URL
        self.login_url = BOSS_LOGIN_URL
        self.recommend_url = BOSS_RECOMMEND_URL
        self.security_url = BOSS_SECURITY_CHECK_URL

        # saved cookies for login persistence
        self.cookies = []
        self.cookies_file = "cookies.json"

    def load_cookies_from_file(self):
        """
        从文件加载 cookies
        """
        if not os.path.exists(self.cookies_file):
            logger.info("Cookies 文件不存在，跳过加载。")
            return
        with open(self.cookies_file, "r") as f:
            self.cookies = json.load(f)
        logger.info("Cookies 已加载。")
        self.page.context.add_cookies(self.cookies)

    def save_cookies_to_file(self):
        """
        将 cookies 保存到文件
        """
        import json, os

        self.cookies = self.page.context.cookies()
        # create the file if it doesn't exist

        if not os.path.exists(self.cookies_file):
            with open(self.cookies_file, "w") as f:
                f.close()
        with open(self.cookies_file, "w") as f:
            json.dump(self.cookies, f)
        logger.info("Cookies 已保存。")

    def _close_email_popup(self):
        """
        检测并关闭“设置邮箱”弹窗
        """
        try:
            popup_locator = self.page.locator(
                "div.dialog-container:has-text('尚未设置邮箱验证')"
            )

            popup_locator.wait_for(state="visible", timeout=5000)

            logger.info("检测到“设置邮箱”弹窗，正在关闭...")
            close_button = popup_locator.locator("i.icon-close")
            close_button.click()
            logger.info("弹窗已关闭。")
        except Exception:
            logger.info("未检测到“设置邮箱”弹窗，继续执行。")

    def login(self):
        """
        执行登录操作，通过扫描二维码登录
        """
        logger.info("正在打开登录页面...")
        self.load_cookies_from_file()
        self.page.goto(self.login_url)
        self.page.wait_for_load_state("networkidle")

        if self.recommend_url in self.page.url or self.page.url in self.base_url:
            logger.info("已检测到已登录状态，跳过登录。")
            logger.info(f"当前URL: {self.page.url}")
            self._close_email_popup()
            return
        else:
            logger.info(f"未检测到登录状态，开始登录流程... 当前URL: {self.page.url}")

        max_trials = 5

        logger.info("请准备扫描二维码...")

        def _switch_to_qr_login() -> bool:
            """
            切换到二维码登录
            """
            is_qr_code = False

            trials = 5

            while not is_qr_code and trials > 0:
                # 检查是否有二维码登录按钮
                trials -= 1

                # if qr_login_button is .btn-sign-switch.ewm-switch
                # click once, otherwise if it is .btn-sign-switch.phone-switch
                # click twice to switch to QR code login
                time.sleep(1)
                # 检查是否有二维码登录按钮
                phone_switch_button = self.page.locator(".btn-sign-switch.phone-switch")
                if phone_switch_button.is_visible():
                    logger.info("切换到二维码登录...")
                    phone_switch_button.click()
                    time.sleep(1)
                    qr_login_button = self.page.locator(".btn-sign-switch.ewm-switch")
                    if qr_login_button.is_visible():
                        qr_login_button.click()
                        time.sleep(2)
                        if self.page.locator(".qr-img-box").is_visible():
                            is_qr_code = True
                            break
                else:
                    qr_login_button = self.page.locator(".btn-sign-switch.ewm-switch")
                    if qr_login_button.is_visible():
                        logger.info("切换到二维码登录...")
                        qr_login_button.click()
                        time.sleep(2)
                        if self.page.locator(".qr-img-box").is_visible():
                            is_qr_code = True
                            break
            return is_qr_code

        while self.page.url != self.recommend_url and max_trials > 0:
            # 切换到二维码登录
            try:
                max_trials -= 1
                if not _switch_to_qr_login():
                    raise Exception("无法切换到二维码登录，请检查页面结构。")
                # 等待二维码加载完成
                logger.info("等待扫描二维码... (20秒超时)")
                # 等待“扫描成功”的提示出现，设置20秒超时
                expect(
                    self.page.locator(".login-step-title:has-text('扫描成功')")
                ).to_be_visible(timeout=20000)
                logger.info("二维码已扫描！请在手机上确认登录。")

                # 等待页面跳转到推荐页，这表示登录成功
                logger.info("等待手机确认...")
                self.page.wait_for_url(
                    f"{self.recommend_url}*", timeout=60000
                )  # 等待60秒的手机确认
                logger.info("登录成功！")
                break
            except Exception as e:
                # 捕捉到超时异常，意味着20秒内没有扫描
                logger.info(f"二维码未扫描或已过期，正在刷新..., 错误信息: {e}")
                # 刷新二维码的操作是再次点击切换按钮
                phone_switch_button = self.page.locator(".btn-sign-switch.phone-switch")
                if phone_switch_button.is_visible():
                    phone_switch_button.click()  # 切换回密码登录
                    time.sleep(0.5)
                    self.page.locator(
                        ".btn-sign-switch.ewm-switch"
                    ).click()  # 再次切换回二维码登录以刷新
                else:
                    # 如果页面结构发生意想不到的变化，直接刷新页面
                    self.page.reload()

                # 在循环的下一次迭代中，将重新等待扫描

        # 最终确认是否真的跳转成功
        if self.recommend_url in self.page.url or self.security_url in self.page.url:
            logger.info(f"已成功登录并跳转到页面: {self.recommend_url}")
            self.save_cookies_to_file()
            self._close_email_popup()
        else:
            raise Exception("登录失败，未能跳转到指定页面。当前url: " + self.page.url)
