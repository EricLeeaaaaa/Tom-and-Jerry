import os
import openai
from dotenv import load_dotenv
from colorama import Fore, Style, init
import time
import re
import json
from datetime import datetime
import tiktoken
import sys
import signal
import readchar  # 引入 readchar

# 初始化colorama
init()

# 加载环境变量
load_dotenv()

# 角色图标
ICONS = {
    "tom": "🔵",  # Tom
    "jerry": "🔴",  # Jerry
    "system": "🔧",  # 系统消息
    "cursor": "➤"  # 选择光标
}

# 枚举 AI 角色名
AI_NAMES = {
    "tom": "Tom",
    "jerry": "Jerry"
}

def stream_print(text, color=None, delay=0.03):
    """流式打印文本"""
    if color:
        sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    if color:
        sys.stdout.write(Style.RESET_ALL)
    sys.stdout.write('\n')
    sys.stdout.flush()

def clear_lines(num_lines):
    """清除指定行数的内容"""
    if os.name == 'nt':
        os.system('cls')
    else:
        for _ in range(num_lines):
            sys.stdout.write('\033[F')  # 光标上移一行
            sys.stdout.write('\033[K')  # 清除该行

def display_menu(options, selected):
    """显示菜单并返回选择的选项"""
    num_options = len(options)
    output = ""
    for i, option in enumerate(options):
        if i == selected:
            output += f"{ICONS['cursor']} {Fore.CYAN}{option}{Style.RESET_ALL}\n"
        else:
            output += f"  {option}\n"
    clear_lines(num_options if selected != -1 else 0)
    sys.stdout.write(output)
    sys.stdout.flush()

class AIModel:
    def __init__(self, api_key, api_base=None, model=None):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=api_base or "https://api.openai.com/v1"
        )
        self.model = model or "gpt-3.5-turbo"
        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            print(f"Warning: Could not automatically map '{self.model}' to a tokenizer. Using 'cl100k_base' as a fallback.")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text):
        """计算文本的token数量"""
        return len(self.encoding.encode(text))

    def get_stream_response(self, messages, temperature=0.7, max_tokens=None):
         """获取流式响应"""
         try:
              response = self.client.chat.completions.create(
                  model=self.model,
                  messages=messages,
                  temperature=temperature,
                  max_tokens=max_tokens,
                  stream=True # 启用流式输出
              )
              return response
         except Exception as e:
             print(f"{Fore.RED}Error in get_stream_response: {str(e)}{Style.RESET_ALL}")
             return None


class ChatRecord:
    def __init__(self, topic, timestamp, chat_history):
        self.topic = topic
        self.timestamp = timestamp
        self.chat_history = chat_history

    @staticmethod
    def save_chat(topic, chat_history):
        """保存聊天记录"""
        record = {
            "topic": topic,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chat_history": chat_history,
        }

        # 确保存储目录存在
        os.makedirs("chats", exist_ok=True)

        # 生成文件名
        filename = f"chats/chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # 保存记录
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        return filename

    @staticmethod
    def load_chats():
        """加载所有聊天记录"""
        chats = []
        if not os.path.exists("chats"):
            return chats

        for filename in os.listdir("chats"):
            if filename.endswith(".json"):
                with open(os.path.join("chats", filename), "r", encoding="utf-8") as f:
                    record = json.load(f)
                    chats.append(record)

        # 按时间戳排序
        chats.sort(key=lambda x: x["timestamp"], reverse=True)
        return chats

class AIChat:
    def __init__(self):
        # 初始化 Tom 模型
        tom_api_key = os.getenv("OPENAI_API_KEY_TOM")
        tom_api_base = os.getenv("OPENAI_API_BASE_URL_TOM")
        tom_model = os.getenv("OPENAI_API_MODEL_TOM", "gpt-3.5-turbo")
        self.tom_model = AIModel(tom_api_key, tom_api_base, tom_model)

        # 初始化 Jerry 模型
        jerry_api_key = os.getenv("OPENAI_API_KEY_JERRY")
        jerry_api_base = os.getenv("OPENAI_API_BASE_URL_JERRY")
        jerry_model = os.getenv("OPENAI_API_MODEL_JERRY", "gpt-3.5-turbo")
        self.jerry_model = AIModel(jerry_api_key, jerry_api_base, jerry_model)

        self.is_running = True
        self.chat_history = []

    def calculate_read_time(self, text):
        """计算阅读时间（秒）"""
        clean_text = re.sub(r'[^\w\s]', '', text)
        char_count = len(clean_text)
        read_time = char_count / 4
        return max(2, min(10, read_time))

    def get_chat_response(self, ai_role, topic, context):
        """获取AI回应"""
        try:
            if ai_role == "tom":
                ai_model = self.tom_model
                prompt = f"你是一个友好的AI助手，名叫Tom。我们正在讨论'{topic}'。请根据之前的对话内容继续对话，你是Tom。"
            else:  # ai_role == "jerry"
                ai_model = self.jerry_model
                prompt = f"你是一个有思考深度的AI助手，名叫Jerry。我们正在讨论'{topic}'。请根据之前的对话内容继续对话，你是Jerry。"

            print(f"\n{ICONS['system']} {Fore.YELLOW}请求 AI ({AI_NAMES[ai_role]}):{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Prompt: {prompt}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Context: {context}{Style.RESET_ALL}")
            # 计算输入token
            input_tokens = ai_model.count_tokens(prompt + context)

            # 获取流式响应
            response_stream = ai_model.get_stream_response(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": context}
                ],
            )

            if not response_stream:
                print(f"{Fore.RED}Error: No response from API.{Style.RESET_ALL}")
                return None, 0

            # 准备接收完整响应
            full_response = ""

            # 流式输出响应
            icon = ICONS['tom'] if ai_role == "tom" else ICONS['jerry']
            color = Fore.BLUE if ai_role == "tom" else Fore.RED
            sys.stdout.write(f"\n{icon} {color}{AI_NAMES[ai_role]}: {Style.RESET_ALL}")
            sys.stdout.flush()
            start_time = time.time()
            for chunk in response_stream:
                if chunk.choices and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None :
                    content = chunk.choices[0].delta.content
                    full_response += content
                    sys.stdout.write(f"{color}{content}{Style.RESET_ALL}")
                    sys.stdout.flush()
                    time.sleep(0.08)
                if time.time() - start_time > 20: #设置20秒超时
                    raise TimeoutError ("Timeout occurred while reading the stream")


            # 计算输出token并显示
            output_tokens = ai_model.count_tokens(full_response)
            total_tokens = input_tokens + output_tokens
            sys.stdout.write(f" [{total_tokens}]\n")
            sys.stdout.flush()

            return full_response, total_tokens
        except TimeoutError as e:
            print(f"\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            return None, 0
        except Exception as e:
           print(f"\n{Fore.RED}Error in get_chat_response: {str(e)}{Style.RESET_ALL}")
           return None, 0



    def display_chat_history(self, chat_record):
        """显示历史聊天记录"""
        print(f"\n{Fore.CYAN}========= 历史聊天 ========={Style.RESET_ALL}")
        stream_print(f"主题: {chat_record['topic']}", Fore.CYAN)
        stream_print(f"时间: {chat_record['timestamp']}", Fore.CYAN)
        print()

        for entry in chat_record['chat_history']:
            if entry.startswith(AI_NAMES["tom"]):
                stream_print(f"{ICONS['tom']} {entry}", Fore.BLUE)
            elif entry.startswith(AI_NAMES["jerry"]):
                stream_print(f"{ICONS['jerry']} {entry}", Fore.RED)
            time.sleep(0.5)
        print(f"{Fore.CYAN}========================={Style.RESET_ALL}\n")

    def run_chat(self, topic, max_rounds):
        """运行聊天过程"""
        print(f"\n{ICONS['system']} {Fore.GREEN}开始关于 '{topic}' 的AI聊天，最多进行 {max_rounds} 轮对话...{Style.RESET_ALL}")
        print(f"{ICONS['system']} {Fore.YELLOW}按 Ctrl+C 强制终止聊天{Style.RESET_ALL}\n")

        context = f"主题是：{topic}"
        round_num = 1

        try:

            # Tom 先发言
            initial_statement, tokens = self.get_chat_response("tom", topic, f"请针对主题'{topic}' 开启对话。你是Tom。")
            if initial_statement:
                  self.chat_history.append(f"{AI_NAMES['tom']}: {initial_statement}")
                  context += f"\n{AI_NAMES['tom']}: {initial_statement}"
                  time.sleep(self.calculate_read_time(initial_statement))


            while self.is_running and round_num <= max_rounds:
                print(f"\n{ICONS['system']} {Fore.CYAN}=== 第 {round_num} 轮对话 ==={Style.RESET_ALL}")

                # Jerry 回应
                jerry_response, jerry_tokens = self.get_chat_response("jerry", topic, context)
                if not jerry_response:
                    break
                self.chat_history.append(f"{AI_NAMES['jerry']}: {jerry_response}")
                context += f"\n{AI_NAMES['jerry']}: {jerry_response}"
                time.sleep(self.calculate_read_time(jerry_response))

                if round_num >= max_rounds:
                    print(f"\n{ICONS['system']} {Fore.YELLOW}已达到最大对话轮数，聊天结束。{Style.RESET_ALL}")
                    break

                round_num += 1

                # Tom 回应
                tom_response, tom_tokens = self.get_chat_response("tom", topic, context)
                if not tom_response:
                    break
                self.chat_history.append(f"{AI_NAMES['tom']}: {tom_response}")
                context += f"\n{AI_NAMES['tom']}: {tom_response}"
                time.sleep(self.calculate_read_time(tom_response))

                if round_num > max_rounds:  # 再次检查，防止 max_rounds 设置过小时，Tom 又回复了一句
                    print(f"\n{ICONS['system']} {Fore.YELLOW}已达到最大对话轮数，聊天结束。{Style.RESET_ALL}")
                    break
                round_num += 1

        except KeyboardInterrupt:
            print(f"\n\n{ICONS['system']} {Fore.YELLOW}聊天被强制终止{Style.RESET_ALL}")

        except Exception as e:
            print(f"\n{ICONS['system']} {Fore.RED}发生错误: {str(e)}{Style.RESET_ALL}")

        finally:
            # 保存聊天记录
           filename = ChatRecord.save_chat(topic, self.chat_history)
           print(f"{ICONS['system']} {Fore.GREEN}聊天记录已保存至: {filename}{Style.RESET_ALL}")

def signal_handler(sig, frame):
    print(f"\n\n{ICONS['system']} {Fore.YELLOW}强制停止，感谢使用AI聊天系统，再见！{Style.RESET_ALL}")
    sys.exit(0)

def get_key():
    """使用 readchar 获取按键输入，并处理转义序列"""
    key = readchar.readkey()
    if key == readchar.key.UP:
        return 'up'
    elif key == readchar.key.DOWN:
        return 'down'
    elif key == readchar.key.ENTER:
        return 'enter'
    elif key == readchar.key.CTRL_C:
        raise KeyboardInterrupt  # 直接抛出异常给上层处理
    return None


def main():
    ai_chat = AIChat()
    print(f"{ICONS['system']} {Fore.CYAN}欢迎使用AI聊天系统！{Style.RESET_ALL}")
    signal.signal(signal.SIGINT, signal_handler)

    while True:
        options = ["开始新的聊天", "查看历史聊天"]
        selected = 0
        num_options = len(options)
        # 显示初始菜单
        print(f"\n{ICONS['system']} 请使用↑↓键选择，回车确认：")
        display_menu(options, selected)

        while True:
            key = get_key()
            if key == 'up' and selected > 0:
                selected -= 1
                display_menu(options, selected)
            elif key == 'down' and selected < num_options - 1:
                selected += 1
                display_menu(options, selected)
            elif key == 'enter':
                display_menu(options,selected)
                clear_lines(1)
                break

        if selected == 0:  # 开始新的聊天
            topic = input(f"\n{Fore.YELLOW}请输入聊天主题: {Style.RESET_ALL}")
            while True:
                try:
                    max_rounds = int(input(f"\n{Fore.YELLOW}请输入最大对话轮数: {Style.RESET_ALL}"))
                    if max_rounds > 0:
                        break
                    else:
                         print(f"{Fore.RED}轮数必须是正整数。{Style.RESET_ALL}")
                except ValueError:
                     print(f"{Fore.RED}请输入有效的整数。{Style.RESET_ALL}")
            ai_chat.run_chat(topic, max_rounds)
        else:  # 查看历史聊天
           chats = ChatRecord.load_chats()
           if not chats:
                print(f"\n{ICONS['system']} {Fore.YELLOW}暂无历史聊天记录{Style.RESET_ALL}")
                continue

           print(f"\n{ICONS['system']} 历史聊天记录：")
           chat_options = [f"{record['timestamp']} - {record['topic']}" for record in chats]
           chat_options.append("返回主菜单")
           selected = 0

           while True:
                display_menu(chat_options, selected)
                key = get_key()
                if key == 'up' and selected > 0:
                    selected -= 1
                    display_menu(chat_options,selected)
                elif key == 'down' and selected < len(chat_options) - 1:
                    selected += 1
                    display_menu(chat_options, selected)
                elif key == 'enter':
                    display_menu(chat_options,selected)
                    clear_lines(1)
                    break
                if selected == len(chat_options) - 1:  # 返回主菜单
                     break
                elif selected >= 0:
                    ai_chat.display_chat_history(chats[selected])
                    input(f"\n{Fore.YELLOW}按回车键返回...{Style.RESET_ALL}")
                    break


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
         print(f"\n{ICONS['system']} {Fore.RED}发生错误: {str(e)}{Style.RESET_ALL}")
