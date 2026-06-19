import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def validate(self):
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY 未设置。请创建 .env 文件并填入 API Key，"
                "或设置环境变量 OPENAI_API_KEY。"
            )


settings = Settings()
