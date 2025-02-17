import logging
import requests
import base64
import json
import yaml
import os
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost

@register(name="FofaQuery", description="为LangBot提供FOFA资产查询功能", version="0.2.3", author="Assistant")
class FofaQueryPlugin(Plugin):
    cfg: dict = None
    plugin_host: PluginHost = None

    def __init__(self, plugin_host: PluginHost):
        self.plugin_host = plugin_host
        if not os.path.exists("plugins/FofaPlugin-master/fofa_config.yaml"):
            raise FileNotFoundError("fofa_config.yaml not found. Please create this file with your FOFA API credentials.")
        
        with open("plugins/FofaPlugin-master/fofa_config.yaml", "r", encoding="utf-8") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)

    @llm_func(name="fofa_query")
    async def fofa_query(self, query,brief_len: str, size: int = 100) -> str:
        """Call this function to Use Fofa API Search the things and return,input two things brief_len means the statement in fofa ,example:"port =80" size means default result number example: 10.

        Args:
            brief_len: FOFA search statement, like "port=80",DO NOT INPUT EVERYTHING IN HERE.
            size: Number of results to return, default is 100, maximum is 10000.

        Returns:
            FOFA查询结果的AI生成摘要，或查询失败时的错误消息。
        """
        try:
            email = self.cfg['fofa_email']
            key = self.cfg['fofa_key']
            
            query_str = brief_len
            
            base64_query = base64.b64encode(query_str.encode()).decode()
            
            url = f"https://fofa.info/api/v1/search/all?email={email}&key={key}&qbase64={base64_query}&size={size}"
            
            with open("fofa_queries.log", "a", encoding="utf-8") as f:
                f.write(f"Query: {query_str}\n")
                f.write(f"Brief_len: {brief_len}\n")
                f.write(f"Size: {size}\n")
                f.write(f"URL: {url}\n")

            response = requests.get(url)
            response.raise_for_status()
            
            result = response.json()
            result_json = json.dumps(result, ensure_ascii=False, indent=2)
            
            prompt = f"""我刚刚使用FOFA API进行了以下查询："{query_str}"
            查询结果如下：
            {result_json}
            
            请分析这些结果，并提供一个简洁的摘要，包括：
            1. 查询到的资产总数
            2. 主要的资产类型或特征
            3. 任何有趣或值得注意的发现
            4. 可能的安全隐患或建议（如果有的话）
            
            请用通俗易懂的语言总结，不要直接列出原始数据。摘要长度大约为{brief_len}字。"""
            
            
            return prompt
        except Exception as e:
            return f"Error in FOFA query: {str(e)}"

    def __del__(self):
        pass

__functions__ = [FofaQueryPlugin.fofa_query]