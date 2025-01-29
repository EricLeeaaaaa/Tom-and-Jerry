# Tom and Jerry

Tom and Jerry 是一个基于 OpenAI API 的多轮对话聊天系统，支持保存聊天记录和查看历史记录。该项目旨在提供一个友好且有趣的聊天体验，用户可以作为观察者观看两个虚拟角色（Tom 和 Jerry）之间的互动。

## 功能特点

- **虚拟角色互动**：Tom 和 Jerry 将围绕指定主题进行多轮对话，用户可以观察他们的互动。
- **聊天记录保存**：自动保存每次聊天的记录，方便后续查看。
- **历史记录查看**：支持加载和查看历史聊天记录。
- **流式输出**：对话内容以流式方式输出，增强互动体验。

## 安装与运行

### 1. 克隆项目

```bash
git clone https://github.com/EricLeeaaaaa/Tom-and-Jerry.git
cd Tom-and-Jerry
```

### 2. 安装依赖

确保已安装 Python 3.8 或更高版本，然后运行以下命令安装依赖：

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，替换示例值：
- 将 `sk-your-tom-api-key-here` 替换为 Tom 的 OpenAI API 密钥
- 将 `sk-your-jerry-api-key-here` 替换为 Jerry 的 OpenAI API 密钥

注意：`.env` 文件包含敏感信息，已在 .gitignore 中配置，不会被提交到代码仓库。

### 4. 运行项目

运行以下命令启动聊天系统：

```bash
python main.py
```

## 使用说明

1. 启动程序后，您可以选择开始新的聊天或查看历史聊天记录。
2. 在新的聊天中，输入主题并设置最大对话轮数。
3. 聊天过程中，Tom 和 Jerry 将轮流发言，您可以观察他们的对话。
4. 聊天结束后，记录会自动保存到 `chats` 文件夹中。

## 依赖库

- `openai`：与 OpenAI API 交互。
- `dotenv`：加载环境变量。
- `colorama`：提供终端颜色支持。
- `tiktoken`：处理 OpenAI 模型的 token 编码。
- `readchar`：处理键盘输入。

## 文件结构

```
Tom-and-Jerry/
├── main.py          # 主程序
├── README.md        # 项目说明
├── .env.example     # 环境变量配置模板
├── .env             # 环境变量配置（本地）
├── requirements.txt # 项目依赖
└── chats/           # 聊天记录存储目录
```

## 贡献

欢迎提交 Issue 或 Pull Request 来改进本项目。

## 许可证

本项目采用 MIT 许可证，详情请参阅 [LICENSE](LICENSE) 文件。