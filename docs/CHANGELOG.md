# 更新日志

## v1.0.0 (2026-05-27)

### 新增功能
- 系统托盘集成
- 浮动单词窗口
- 学习模式（学习新单词）
- 复习模式（间隔重复算法）
- 测试模式（英译中、中译英、听写）
- 单词本功能
- 学习统计
- 自动弹词功能
- 可拖拽浮动窗口
- 自定义设置

### 单词数据库
- CET-4 词汇：3739 个单词（3728 含例句）
- CET-6 词汇：1615 个单词（1554 含例句）
- 自定义词汇：78 个单词
- 总计：5432 个单词

### 工具脚本
- `tools/add_words.py`：添加新单词
- `tools/download_words.py`：下载更多单词
- `tools/check_words.py`：单词检查
- `tools/check_quality.py`：词库质量检查
- `tests/test_app.py`：测试脚本
- `tests/test_full.py`：完整测试套件

### 文档
- `docs/CHANGELOG.md`：更新日志（本文件）
- `docs/PROJECT_SUMMARY.md`：项目总结

### 技术实现
- Python 3.7+
- pystray：系统托盘图标
- Pillow：图像处理
- tkinter：GUI 界面
- sqlite3：本地数据库
