"""
Appium MCP Server - Mobile automation testing via Model Context Protocol.

这个包提供了一个基于MCP协议的Appium服务器，
允许AI助手通过标准化接口进行移动设备自动化测试。
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .server import AppiumMCPServer

__all__ = ["AppiumMCPServer", "__version__"] 