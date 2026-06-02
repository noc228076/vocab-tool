# 四六级背单词小工具

一个轻量级的 Windows 系统托盘背单词工具，支持 CET-4/CET-6 词汇学习。

## 功能特点

- **系统托盘运行**：最小化到系统托盘，不影响正常工作
- **自动弹词**：定时弹出单词卡片，利用碎片时间学习
- **浮动窗口**：可拖拽的浮动单词窗口，支持自动隐藏
- **多种学习模式**：
  - 学习模式：学习新单词
  - 复习模式：基于间隔重复算法的智能复习
  - 测试模式：英译中、中译英、听写测试
- **单词本**：收藏重要单词，随时复习
- **学习统计**：记录学习进度、正确率、学习时间
- **间隔重复**：基于 SM-2 算法的科学记忆方法

## 安装使用

### 方式一：直接运行

1. 确保已安装 Python 3.7+
2. 双击 `启动背单词.bat`
3. 首次运行会自动安装依赖

### 方式二：手动安装

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行程序
python vocab_app.py
```

## 使用说明

1. 启动后，程序会最小化到系统托盘
2. 右键点击托盘图标，可以看到功能菜单
3. 选择「学习模式」开始学习新单词
4. 选择「复习模式」复习已学单词
5. 选择「测试模式」进行单词测试
6. 选择「设置」可以调整弹词间隔、窗口位置等

## 快捷操作

- **自动弹词**：默认每 5 分钟弹出一个单词
- **浮动窗口**：可拖拽到任意位置
- **单词本**：点击「收藏」按钮添加到单词本

## 文件说明

- `vocab_app.py` - 主程序
- `words.json` - 单词数据库（CET-4/CET-6）
- `vocab_progress.db` - 学习进度数据库（自动生成）
- `requirements.txt` - Python 依赖
- `启动背单词.bat` - Windows 启动脚本
- `merge_words.py` - 合并单词文件
- `add_words.py` - 添加新单词
- `download_words.py` - 下载更多单词
- `word_stats.py` - 单词统计
- `test_app.py` - 测试脚本

## 自定义单词

### 方式一：交互式添加

```bash
python add_words.py
```

然后按格式输入：`单词 | 音标 | 释义 | 例句`

### 方式二：编辑 JSON 文件

编辑 `words.json` 文件可以添加或修改单词：

```json
{
  "cet4": [
    {
      "word": "example",
      "phonetic": "/ɪɡˈzæmpl/",
      "meaning": "n. 例子；榜样",
      "example": "This is an example.",
      "category": "cet4"
    }
  ]
}
```

### 方式三：批量导入

创建文本文件，每行一个单词，格式：`单词|音标|释义|例句`

然后运行：
```bash
python add_words.py words.txt cet4
```

## 系统要求

- Windows 7/10/11
- Python 3.7+
- 约 50MB 磁盘空间

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
