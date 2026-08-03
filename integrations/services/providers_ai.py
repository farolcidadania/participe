from integrations.models import APIKeys, AIUsage
from integrations.services.discord import DiscordService
from openai import OpenAI


import os
import csv
import logging

logger = logging.getLogger(__name__)

discord = DiscordService(username="AI services", dev=True) # controle de qualidade nas respostas das IAs

class AIProvidersService:

    """
    ele vai receber o prompt pronto e enviar para o provedor padrão,
    retornando o conteúdo gerado de forma agnóstica do provedor.
    """
    def __init__(self):
        # Busca a única chave definida como padrão
        default_key = APIKeys.objects.filter(active=True, is_default=True).first()
        
        if not default_key:
            default_key = APIKeys.objects.filter(active=True).first()
            if not default_key:
                erro_msg = "Nenhum provedor de IA padrão (is_default) configurado no banco de dados."
                discord.log_danger(erro_msg)
                raise ValueError(erro_msg)
            
        self.api_key_obj = default_key
        self.provider_name = default_key.service.lower()
        self.api_key = default_key.get_decrypted_api_key()

    def execute_prompt(self, prompt, response_format={"type": "json_object"}):
        """
        Função principal que executa o prompt no provedor configurado.
        Pode ser facilmente adaptada para suportar múltiplos provedores.
        """
        try:
            if "openai" in self.provider_name:
                return self._execute_openai(prompt, response_format)
            else:
                logger.warning(f"Provedor '{self.provider_name}' não suportado explicitamente, tentando como openai.")
                return self._execute_openai(prompt, response_format)

        except Exception as e:
            discord.log_danger(f"Erro ao executar prompt: {e}")
            raise e

    def _execute_openai(self, prompt, response_format):
        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format=response_format,
                messages=[{"role": "user", "content": prompt}],
                timeout=15.0
            )
        except Exception as e_req:
            logger.error(f"Falha de comunicação com a OpenAI: {e_req}")
            raise e_req
            
        import json
        content = response.choices[0].message.content
        try:
            resp_json = json.loads(response.model_dump_json())
        except AttributeError:
            resp_json = {"content": content}

        AIUsage.objects.create(
            from_api=self.api_key_obj,
            messages=[{"role": "user", "content": prompt}],
            response=resp_json,
            tokens_prompt=response.usage.prompt_tokens,
            tokens_response=response.usage.completion_tokens,
            tokens_total=response.usage.total_tokens,
        )
        
        return content

