import re
import aiohttp
import asyncio
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger


@register("constellation", "AstroDev", "星座运势查询插件", "1.0.0", "https://github.com/your-repo")
class ConstellationPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.CONSTELLATION_URL = "https://api.vvhan.com/api/horoscope"
        self.session = aiohttp.ClientSession()
        self.ZODIAC_MAPPING = {
            '白羊座': 'aries',
            '金牛座': 'taurus',
            '双子座': 'gemini',
            '巨蟹座': 'cancer',
            '狮子座': 'leo',
            '处女座': 'virgo',
            '天秤座': 'libra',
            '天蝎座': 'scorpio',
            '射手座': 'sagittarius',
            '摩羯座': 'capricorn',
            '水瓶座': 'aquarius',
            '双鱼座': 'pisces'
        }

    async def terminate(self):
        """关闭aiohttp会话"""
        await self.session.close()
        logger.info("星座插件会话已关闭")

    def constellation_check_keyword(self, content):
        """检查星座关键字"""
        horoscope_match = re.match(r'^([\u4e00-\u9fa5]{2}座)$', content)
        return horoscope_match

    async def constellation_request(self, zodiac_english):
        """星座请求函数"""
        try:
            # 设置请求参数
            params = {"type": zodiac_english, "time": "today"}

            async with self.session.get(self.CONSTELLATION_URL, params=params) as response:
                if response.status != 200:
                    err_str = f"API请求失败: HTTP {response.status}"
                    logger.error(err_str)
                    return err_str

                response_data = await response.json()

                if response_data.get("success"):
                    # 解析并格式化运势数据
                    data = response_data['data']
                    constellation_text = (
                        f"✨ {data['title']}今日运势 ✨\n"
                        f"📅 日期：{data['time']}\n\n"
                        f"💡【每日建议】\n"
                        f"宜：{data['todo']['yi']}\n"
                        f"忌：{data['todo']['ji']}\n\n"
                        f"📊【运势指数】\n"
                        f"总运势：{data['index']['all']}\n"
                        f"爱情：{data['index']['love']}\n"
                        f"工作：{data['index']['work']}\n"
                        f"财运：{data['index']['money']}\n"
                        f"健康：{data['index']['health']}\n\n"
                        f"🍀【幸运提示】\n"
                        f"数字：{data['luckynumber']}\n"
                        f"颜色：{data['luckycolor']}\n"
                        f"星座：{data['luckyconstellation']}\n\n"
                        f"🔔【简评】\n{data['shortcomment']}"
                    )
                    logger.debug(f"星座运势数据: {constellation_text}")
                    return constellation_text
                else:
                    err_str = f"API返回错误: {response_data.get('message', '未知错误')}"
                    logger.error(err_str)
                    return err_str

        except aiohttp.ClientError as e:
            err_str = f"网络请求错误: {str(e)}"
            logger.error(err_str)
            return err_str
        except Exception as err:
            err_str = f"处理错误: {str(err)}"
            logger.error(err_str)
            return err_str

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_constellation(self, event: AstrMessageEvent):
        """处理星座运势请求"""
        content = event.message_str.strip()

        if self.constellation_check_keyword(content):
            logger.debug(f"[星座插件] 收到请求: {content}")

            if content in self.ZODIAC_MAPPING:
                zodiac_english = self.ZODIAC_MAPPING[content]
                result = await self.constellation_request(zodiac_english)
                yield event.plain_result(result)
            else:
                yield event.plain_result("暂不支持该星座查询，请输入正确的星座名称如'白羊座'")

            # 中断事件处理流程
            event.stop_event()  # 停止事件传播，防止其他插件处理相同消息