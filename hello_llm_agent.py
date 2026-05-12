import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class HelloLlmAgent:
    def __init__(self, model: str = None, base_url: str = None, api_key: str = None):
        """
        初始化 LLM 客户端
        """
        self.model = model or os.getenv("OPENAI_MODEL_ID")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not all([self.model, self.base_url, self.api_key]):
            raise ValueError("❌ 请在 .env 中配置 OPENAI_MODEL_ID / BASE_URL / API_KEY")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def think(self, user_input: str, system_prompt: str = None, temperature: float = 0.7) -> str:
        """
        调用 LLM（非流式）
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": user_input})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=False
            )

            content = response.choices[0].message.content

            return content.strip() if content else "..."

        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            return "我暂时无法回答"

#调用示例：
if __name__ == "__main__":
    try:
        llmClient = HelloLlmAgent()
        Messages=input().split()[0]
        print("--- 调用LLM ---")
        responseText = llmClient.think(Messages)
        if responseText:
            print("\n\n--- 完整模型响应 ---")
            print(responseText)

    except ValueError as e:
        print(e)
