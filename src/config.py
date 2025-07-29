import logging

# Global variables
BOSS_BASE_URL = "https://www.zhipin.com/"
BOSS_LOGIN_URL = "https://www.zhipin.com/web/user/"
BOSS_RECOMMEND_URL = "https://www.zhipin.com/web/geek/job-recommend"
BOSS_SECURITY_CHECK_URL = "https://www.zhipin.com/web/common/security-check.html"
INTERESTING_JOBS_URL = "https://www.zhipin.com/web/geek/recommend?tab=4&sub=1&page=1&tag=4&ka=header-personal"

# Logger, highlighting events
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

