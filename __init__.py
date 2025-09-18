"""
视频编辑节点包
支持视频裁切、预览等功能
"""

from .edit_video import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# 设置Web目录 - ComfyUI会自动加载此目录下的所有.js文件
WEB_DIRECTORY = "./web/js"

# 版本信息
__version__ = "1.0.0"
__author__ = "Shenglin"
__description__ = "视频编辑工具包：智能视频裁切、预览功能"

# 导出必要的变量供ComfyUI加载
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

print("🎬 视频编辑节点包已加载")
print(f"📝 包含节点: {len(NODE_CLASS_MAPPINGS)} 个")
print(f"🌐 Web界面目录: {WEB_DIRECTORY}")