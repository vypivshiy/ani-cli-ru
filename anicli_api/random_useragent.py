"""simple useragent generator"""

from random import choice

CHROME_VERSIONS = (
    '98.0.4758.108', '98.0.4758.107', '98.0.4758.106', '97.0.4692.108', '98.0.4758.105', '98.0.4758.104',
    '98.0.4758.103', '98.0.4758.102', '98.0.4758.101', '98.0.4758.100', '98.0.4758.99', '97.0.4692.107', '98.0.4758.98',
    '96.0.4664.194',
    '98.0.4758.97', '96.0.4664.193', '98.0.4758.96', '96.0.4664.192', '97.0.4692.106', '97.0.4692.105', '96.0.4664.183',
    '97.0.4692.104', '97.0.4692.103', '96.0.4664.181', '96.0.4664.180', '96.0.4664.179', '96.0.4664.178',
    '96.0.4664.177',
    '97.0.4692.102', '96.0.4664.176', '97.0.4692.101', '96.0.4664.175', '97.0.4692.100', '96.0.4664.174',
    '97.0.4692.99',
    '97.0.4692.98', '97.0.4692.97'
)

MOBILE_STRINGS = (
    "(Linux; Android 6.0; Nexus 5)",
    "(Linux; Android 7.0; Redmi Note 7 Pro)",
    "(Linux; Android 8.1.0; Redmi Note 8 Pro)",
    "(Linux; Android 9.0.0; Redmi Note 9 Pro)",
    "(Linux; Android 6.0; SM-A710F)",
    "(Linux; Android 6.0; SAMSUNG SM-C9000)"
)

DESKTOP_STRINGS = (
    "(Windows NT 10.0; Win64; x64)",
    "(Windows NT 11.0; Win64; x64)",
    "(X11; Linux x86_64)",
)


class Agent:
    """Simple UserAgent string generator noname chromium based browser for desktop or mobile

    Basic Usage::

      >>> from anicli_ru.utils.random_agent import Agent
      >>> agent = Agent.desktop()
      Mozilla/5.0 (X11; Linux x86_64) ...

      >>> agent = Agent.mobile()
      Mozilla/5.0 (Linux; Android 6.0; Nexus 5) ...
    """
    @classmethod
    def mobile(cls) -> str:
        """Generate chromium based useragent for mobile

        :return: useragent string
        """
        device = choice(MOBILE_STRINGS)
        chrome = choice(CHROME_VERSIONS)
        return f"Mozilla/5.0 {device} AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Mobile Safari/537.36"

    @classmethod
    def desktop(cls) -> str:
        """Generate chromium based useragent for desktop

        :return: useragent string"""
        device = choice(DESKTOP_STRINGS)
        chrome = choice(CHROME_VERSIONS)
        return f"Mozilla/5.0 {device} AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome} Safari/537.36"

    @classmethod
    def random(cls) -> str:
        """Generate desktop or mobile useragent

        :return: useragent string
        """
        return choice((cls.mobile, cls.desktop))()
