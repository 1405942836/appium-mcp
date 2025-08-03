"""
UI自动化工具。

提供元素查找、点击、输入、手势等UI操作功能。
"""

import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ..utils.helpers import encode_image_to_base64, sanitize_filename
from .base import UIAutomationTool


class FindElementTool(UIAutomationTool):
    """查找UI元素。"""

    @property
    def name(self) -> str:
        return "find_element"

    @property
    def description(self) -> str:
        return "查找单个UI元素"

    @property
    def parameters(self) -> Dict[str, Any]:
        params = {
            "session_id": {
                "type": "string",
                "description": "会话ID",
                "minLength": 1,
            },
            "timeout": {
                "type": "integer",
                "description": "查找超时时间（秒）",
                "minimum": 1,
                "maximum": 60,
                "optional": True,
            },
        }
        params.update(self._get_common_locator_parameters())
        return params

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行元素查找。"""
        session_id = arguments["session_id"]
        locator_type = arguments["locator_type"]
        locator_value = arguments["locator_value"]
        timeout = arguments.get("timeout", 10)

        session, lock = await self.get_session_with_lock(session_id)
        
        async with lock:
            try:
                # 获取定位器
                by = self._get_appium_by(locator_type)
                
                # 等待元素出现
                wait = WebDriverWait(session.driver, timeout)
                element = wait.until(EC.presence_of_element_located((by, locator_value)))

                # 获取元素信息
                element_info = {
                    "element_id": element.id,
                    "tag_name": element.tag_name,
                    "text": element.text,
                    "enabled": element.is_enabled(),
                    "displayed": element.is_displayed(),
                    "selected": element.is_selected(),
                    "location": element.location,
                    "size": element.size,
                    "rect": element.rect,
                }

                # 获取属性
                try:
                    element_info["attributes"] = {
                        "content-desc": element.get_attribute("content-desc"),
                        "resource-id": element.get_attribute("resource-id"),
                        "class": element.get_attribute("class"),
                        "package": element.get_attribute("package"),
                        "checkable": element.get_attribute("checkable"),
                        "checked": element.get_attribute("checked"),
                        "clickable": element.get_attribute("clickable"),
                        "focusable": element.get_attribute("focusable"),
                        "focused": element.get_attribute("focused"),
                        "scrollable": element.get_attribute("scrollable"),
                        "long-clickable": element.get_attribute("long-clickable"),
                    }
                except Exception:
                    element_info["attributes"] = {}

                return {
                    "found": True,
                    "element": element_info,
                    "locator": {
                        "type": locator_type,
                        "value": locator_value,
                    },
                }

            except Exception as e:
                return {
                    "found": False,
                    "error": str(e),
                    "locator": {
                        "type": locator_type,
                        "value": locator_value,
                    },
                }

    def _get_appium_by(self, locator_type: str) -> str:
        """获取Appium定位器类型。"""
        mapping = {
            "id": AppiumBy.ID,
            "name": AppiumBy.NAME,
            "class_name": AppiumBy.CLASS_NAME,
            "tag_name": AppiumBy.TAG_NAME,
            "xpath": AppiumBy.XPATH,
            "css_selector": AppiumBy.CSS_SELECTOR,
            "accessibility_id": AppiumBy.ACCESSIBILITY_ID,
            "android_uiautomator": AppiumBy.ANDROID_UIAUTOMATOR,
            "ios_predicate": AppiumBy.IOS_PREDICATE,
            "ios_class_chain": AppiumBy.IOS_CLASS_CHAIN,
        }
        return mapping.get(locator_type, AppiumBy.XPATH)


class ClickElementTool(UIAutomationTool):
    """点击UI元素。"""

    @property
    def name(self) -> str:
        return "click_element"

    @property
    def description(self) -> str:
        return "点击指定的UI元素"

    @property
    def parameters(self) -> Dict[str, Any]:
        params = {
            "session_id": {
                "type": "string",
                "description": "会话ID",
                "minLength": 1,
            },
            "timeout": {
                "type": "integer",
                "description": "查找元素超时时间（秒）",
                "minimum": 1,
                "maximum": 60,
                "optional": True,
            },
        }
        params.update(self._get_common_locator_parameters())
        return params

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行元素点击。"""
        session_id = arguments["session_id"]
        locator_type = arguments["locator_type"]
        locator_value = arguments["locator_value"]
        timeout = arguments.get("timeout", 10)

        session, lock = await self.get_session_with_lock(session_id)
        
        async with lock:
            try:
                # 查找元素
                by = self._get_appium_by(locator_type)
                wait = WebDriverWait(session.driver, timeout)
                element = wait.until(EC.element_to_be_clickable((by, locator_value)))

                # 点击元素
                element.click()

                return {
                    "success": True,
                    "action": "click",
                    "element_info": {
                        "element_id": element.id,
                        "text": element.text,
                        "location": element.location,
                        "size": element.size,
                    },
                    "locator": {
                        "type": locator_type,
                        "value": locator_value,
                    },
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "action": "click",
                    "locator": {
                        "type": locator_type,
                        "value": locator_value,
                    },
                }

    def _get_appium_by(self, locator_type: str) -> str:
        """获取Appium定位器类型。"""
        mapping = {
            "id": AppiumBy.ID,
            "name": AppiumBy.NAME,
            "class_name": AppiumBy.CLASS_NAME,
            "tag_name": AppiumBy.TAG_NAME,
            "xpath": AppiumBy.XPATH,
            "css_selector": AppiumBy.CSS_SELECTOR,
            "accessibility_id": AppiumBy.ACCESSIBILITY_ID,
            "android_uiautomator": AppiumBy.ANDROID_UIAUTOMATOR,
            "ios_predicate": AppiumBy.IOS_PREDICATE,
            "ios_class_chain": AppiumBy.IOS_CLASS_CHAIN,
        }
        return mapping.get(locator_type, AppiumBy.XPATH)


class InputTextTool(UIAutomationTool):
    """在元素中输入文本。"""

    @property
    def name(self) -> str:
        return "input_text"

    @property
    def description(self) -> str:
        return "在指定的UI元素中输入文本"

    @property
    def parameters(self) -> Dict[str, Any]:
        params = {
            "session_id": {
                "type": "string",
                "description": "会话ID",
                "minLength": 1,
            },
            "text": {
                "type": "string",
                "description": "要输入的文本",
            },
            "clear_first": {
                "type": "boolean",
                "description": "是否先清空现有文本",
                "optional": True,
            },
            "timeout": {
                "type": "integer",
                "description": "查找元素超时时间（秒）",
                "minimum": 1,
                "maximum": 60,
                "optional": True,
            },
        }
        params.update(self._get_common_locator_parameters())
        return params

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行文本输入。"""
        session_id = arguments["session_id"]
        locator_type = arguments["locator_type"]
        locator_value = arguments["locator_value"]
        text = arguments["text"]
        clear_first = arguments.get("clear_first", True)
        timeout = arguments.get("timeout", 10)

        session, lock = await self.get_session_with_lock(session_id)
        
        async with lock:
            try:
                # 查找元素
                by = self._get_appium_by(locator_type)
                wait = WebDriverWait(session.driver, timeout)
                element = wait.until(EC.presence_of_element_located((by, locator_value)))

                # 清空文本（如果需要）
                if clear_first:
                    element.clear()

                # 输入文本
                element.send_keys(text)

                return {
                    "success": True,
                    "action": "input_text",
                    "text": text,
                    "clear_first": clear_first,
                    "element_info": {
                        "element_id": element.id,
                        "text": element.text,
                        "location": element.location,
                        "size": element.size,
                    },
                    "locator": {
                        "type": locator_type,
                        "value": locator_value,
                    },
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "action": "input_text",
                    "text": text,
                    "locator": {
                        "type": locator_type,
                        "value": locator_value,
                    },
                }

    def _get_appium_by(self, locator_type: str) -> str:
        """获取Appium定位器类型。"""
        mapping = {
            "id": AppiumBy.ID,
            "name": AppiumBy.NAME,
            "class_name": AppiumBy.CLASS_NAME,
            "tag_name": AppiumBy.TAG_NAME,
            "xpath": AppiumBy.XPATH,
            "css_selector": AppiumBy.CSS_SELECTOR,
            "accessibility_id": AppiumBy.ACCESSIBILITY_ID,
            "android_uiautomator": AppiumBy.ANDROID_UIAUTOMATOR,
            "ios_predicate": AppiumBy.IOS_PREDICATE,
            "ios_class_chain": AppiumBy.IOS_CLASS_CHAIN,
        }
        return mapping.get(locator_type, AppiumBy.XPATH)


class TakeScreenshotTool(UIAutomationTool):
    """截取屏幕截图。"""

    @property
    def name(self) -> str:
        return "take_screenshot"

    @property
    def description(self) -> str:
        return "截取当前屏幕的截图"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "session_id": {
                "type": "string",
                "description": "会话ID",
                "minLength": 1,
            },
            "filename": {
                "type": "string",
                "description": "截图文件名（可选）",
                "optional": True,
            },
            "format": {
                "type": "string",
                "description": "截图格式",
                "enum": ["png", "jpg"],
                "optional": True,
            },
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行截图。"""
        session_id = arguments["session_id"]
        filename = arguments.get("filename")
        image_format = arguments.get("format", "png")

        session, lock = await self.get_session_with_lock(session_id)
        
        async with lock:
            try:
                # 截取屏幕截图
                screenshot_base64 = session.driver.get_screenshot_as_base64()
                
                # 生成文件名
                if not filename:
                    import time
                    timestamp = int(time.time())
                    device_name = sanitize_filename(session.device_info.name)
                    filename = f"screenshot_{device_name}_{timestamp}.{image_format}"
                else:
                    filename = sanitize_filename(filename)
                    if not filename.endswith(f".{image_format}"):
                        filename += f".{image_format}"

                # 保存截图文件（可选）
                screenshot_path = None
                try:
                    from pathlib import Path
                    screenshots_dir = Path("./screenshots")
                    screenshots_dir.mkdir(exist_ok=True)
                    screenshot_path = screenshots_dir / filename
                    
                    # 解码并保存
                    screenshot_data = base64.b64decode(screenshot_base64)
                    with open(screenshot_path, "wb") as f:
                        f.write(screenshot_data)
                except Exception as save_error:
                    self.logger.warning("Failed to save screenshot file", error=str(save_error))

                return {
                    "success": True,
                    "action": "screenshot",
                    "filename": filename,
                    "file_path": str(screenshot_path) if screenshot_path else None,
                    "base64_data": screenshot_base64,
                    "format": image_format,
                    "device_info": {
                        "device_id": session.device_info.device_id,
                        "platform": session.device_info.platform,
                        "name": session.device_info.name,
                    },
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "action": "screenshot",
                }


class SwipeTool(UIAutomationTool):
    """执行滑动手势。"""

    @property
    def name(self) -> str:
        return "swipe"

    @property
    def description(self) -> str:
        return "在屏幕上执行滑动手势"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "session_id": {
                "type": "string",
                "description": "会话ID",
                "minLength": 1,
            },
            "start_x": {
                "type": "integer",
                "description": "起始X坐标",
                "minimum": 0,
            },
            "start_y": {
                "type": "integer",
                "description": "起始Y坐标",
                "minimum": 0,
            },
            "end_x": {
                "type": "integer",
                "description": "结束X坐标",
                "minimum": 0,
            },
            "end_y": {
                "type": "integer",
                "description": "结束Y坐标",
                "minimum": 0,
            },
            "duration": {
                "type": "integer",
                "description": "滑动持续时间（毫秒）",
                "minimum": 100,
                "maximum": 10000,
                "optional": True,
            },
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行滑动手势。"""
        session_id = arguments["session_id"]
        start_x = arguments["start_x"]
        start_y = arguments["start_y"]
        end_x = arguments["end_x"]
        end_y = arguments["end_y"]
        duration = arguments.get("duration", 1000)

        session, lock = await self.get_session_with_lock(session_id)
        
        async with lock:
            try:
                # 执行滑动
                session.driver.swipe(start_x, start_y, end_x, end_y, duration)

                return {
                    "success": True,
                    "action": "swipe",
                    "start_point": {"x": start_x, "y": start_y},
                    "end_point": {"x": end_x, "y": end_y},
                    "duration": duration,
                }

            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "action": "swipe",
                    "start_point": {"x": start_x, "y": start_y},
                    "end_point": {"x": end_x, "y": end_y},
                    "duration": duration,
                } 