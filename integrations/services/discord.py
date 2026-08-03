from __future__ import annotations
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from ..models import DiscordWebhook

try:
    import requests
except Exception:
    requests = None

import urllib.request
import urllib.error

from django.conf import settings
import logging
from app.version import __version__ as app_version
MAX_FILE_SIZE = 8 * 1024 * 1024 

logger = logging.getLogger(__name__)


class DiscordService:
    """
    Serviço simples para enviar logs para um Discord Webhook usando embeds.
    Lê a URL do webhook de:
      - settings.DISCORD_LOG_WEBHOOK_URL
      - ou da variável de ambiente DISCORD_LOG_WEBHOOK_URL

    Métodos públicos:
      - log_success(message, title=None, fields=None)
      - log_warning(message, title=None, fields=None)
      - log_danger(message, title=None, fields=None)
      - log_info(message, title=None, fields=None)
      - log_file(file_data, title=None, description=None, filename="log.json", fields=None)

    `fields` deve ser uma lista de dicts: [{"name": "Campo", "value": "valor", "inline": False}, ...]
    """

    COLOR_SUCCESS = 0x2ECC71  # verde
    COLOR_WARNING = 0xF1C40F  # amarelo
    COLOR_DANGER = 0xE74C3C   # vermelho
    COLOR_INFO = 0x3498DB     # azul (fallback)

    def __init__(self, username: Optional[str] = None, dev: bool = False):
        self.webhook_url = None
        try:
            # Tenta buscar o webhook no banco de forma segura. 
            # Pode falhar se as migrações (ex: coluna 'dev') ainda não foram aplicadas.
            webhook = DiscordWebhook.objects.filter(is_active=True, dev=dev).first()
            if webhook:
                self.webhook_url = webhook.url
        except Exception:
            # Silencioso: se o banco/tabela/coluna não existir, o serviço apenas não enviará mensagens
            # Isso é crítico para permitir que o 'python manage.py migrate' funcione.
            pass
        self.username = username or getattr(settings, "DISCORD_LOG_USERNAME", "LoggerBot")
        
        # Verificar se está em ambiente de desenvolvimento
        # settings.DEV ou settings.DEBUG (do Django)
        # ou variável de ambiente DEBUG (convertendo string para bool)
        debug_env = os.environ.get("DEBUG", "").lower() in ("true", "1", "yes")
        self.dev = (
            getattr(settings, "DEV", None)
            or getattr(settings, "DEBUG", False)
            or debug_env
        )
        self.version = (
            getattr(settings, "APP_VERSION", None)
            or os.environ.get("APP_VERSION")
            or app_version
        )
        self.environment = str("dev" if self.dev else "prod")
        self.footer_text = f"{self.environment} | {self.version}"
        if not self.webhook_url:
            logger.warning("DiscordService inicializado sem DISCORD_LOG_WEBHOOK_URL — logs para Discord serão ignorados.")

    def log_success(self, message: str, title: Optional[str] = "Sucesso", fields: Optional[List[Dict[str, Any]]] = None):
        return self._send_embed(title=title, description=message, color=self.COLOR_SUCCESS, fields=fields)

    def log_warning(self, message: str, title: Optional[str] = "Aviso", fields: Optional[List[Dict[str, Any]]] = None):
        return self._send_embed(title=title, description=message, color=self.COLOR_WARNING, fields=fields)

    def log_danger(self, message: str, title: Optional[str] = "Erro Crítico", fields: Optional[List[Dict[str, Any]]] = None):
        return self._send_embed(title=title, description=message, color=self.COLOR_DANGER, fields=fields)

    def log_info(self, message: str, title: Optional[str] = "Info", fields: Optional[List[Dict[str, Any]]] = None):
        return self._send_embed(title=title, description=message, color=self.COLOR_INFO, fields=fields)

    def log_file(
        self,
        file_data: Any,
        title: Optional[str] = None,
        description: Optional[str] = None,
        filename: Optional[str] = "log.json",
        fields: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Envia um arquivo via webhook do Discord.
        
        Args:
            file_data: Dados do arquivo. Pode ser dict/list (convertido para JSON),
                      str (texto ou JSON), ou bytes.
            title: Título do embed (opcional). Se None, envia apenas o arquivo.
            description: Descrição do embed (opcional).
            filename: Nome do arquivo a ser enviado (padrão: "log.json").
            fields: Lista de campos para o embed (opcional).
        
        Returns:
            True se enviado com sucesso, False caso contrário.
        """
        return self._send_file(
            file_data=file_data,
            title=title,
            description=description,
            filename=filename,
            fields=fields,
        )

    def _send_file(
        self,
        file_data: Any,
        title: Optional[str],
        description: Optional[str],
        filename: str,
        fields: Optional[List[Dict[str, Any]]],
    ) -> bool:
        """
        Método privado que envia arquivo via webhook.
        Converte entrada para bytes, valida tamanho, e envia via multipart/form-data.
        """
        if not self.webhook_url:
            logger.debug("DiscordService: webhook não configurado — ignorando envio de arquivo.")
            return False

        # Converter file_data para bytes UTF-8
        try:
            if isinstance(file_data, (dict, list)):
                # Converter dict/list para JSON string, depois para bytes
                file_bytes = json.dumps(file_data, ensure_ascii=False, indent=2).encode("utf-8")
            elif isinstance(file_data, str):
                # String direta para bytes
                file_bytes = file_data.encode("utf-8")
            elif isinstance(file_data, bytes):
                # Já é bytes
                file_bytes = file_data
            else:
                # Tentar converter para string e depois bytes
                file_bytes = str(file_data).encode("utf-8")
        except Exception as e:
            logger.exception("DiscordService: falha ao converter file_data para bytes: %s", e)
            return False

        # Validar tamanho
        file_size = len(file_bytes)
        exceeds_limit = file_size > MAX_FILE_SIZE

        # Preparar embed se title fornecido
        embed = None
        if title:
            embed = {
                "title": title or "",
                "description": description or "",
                "color": self.COLOR_INFO,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": self.footer_text},
            }

            if fields:
                embed["fields"] = fields[:25]

            # Se arquivo exceder limite, adicionar preview truncado no embed
            if exceeds_limit:
                preview_text = self._create_preview(file_bytes)
                if not embed.get("description"):
                    embed["description"] = ""
                embed["description"] += f"\n\n⚠️ **Arquivo muito grande ({file_size / 1024 / 1024:.2f} MB)**\n```\n{preview_text}\n```"

        # Se exceder limite e não houver embed, não enviar arquivo
        if exceeds_limit and not embed:
            logger.warning(f"DiscordService: arquivo muito grande ({file_size} bytes) e sem embed — não enviando.")
            return False

        # Se exceder limite mas houver embed, enviar apenas embed
        if exceeds_limit:
            logger.warning(f"DiscordService: arquivo muito grande ({file_size} bytes) — enviando apenas embed com preview.")
            return self._send_embed(
                title=embed["title"],
                description=embed["description"],
                color=embed["color"],
                fields=embed.get("fields"),
            )

        # Enviar arquivo (com ou sem embed)
        try:
            if not requests:
                # Fallback: se não tiver requests, tentar enviar apenas embed se houver
                if embed:
                    logger.warning("DiscordService: requests não disponível — enviando apenas embed (arquivo não enviado).")
                    return self._send_embed(
                        title=embed["title"],
                        description=embed["description"],
                        color=embed["color"],
                        fields=embed.get("fields"),
                    )
                else:
                    logger.warning("DiscordService: requests não disponível e sem embed — não é possível enviar arquivo.")
                    return False

            # Preparar payload para multipart/form-data
            payload = {"username": self.username}

            if embed:
                payload["embeds"] = [embed]

            # Preparar arquivo para upload
            files = {
                "file": (filename, file_bytes, "application/json" if filename.endswith(".json") else "text/plain")
            }

            # Enviar via multipart/form-data
            resp = requests.post(
                self.webhook_url,
                data={"payload_json": json.dumps(payload)},
                files=files,
                timeout=5,
            )

            if resp.status_code in (200, 204):
                return True
            else:
                logger.warning(f"DiscordService: webhook retornou {resp.status_code} - {resp.text}")
                if resp.status_code == 429:
                    logger.warning("DiscordService: rate limited (429).")
                return False

        except Exception as e:
            logger.exception("DiscordService: falha ao enviar arquivo para Discord: %s", e)
            return False

    def _create_preview(self, file_bytes: bytes, max_lines: int = 1000, max_bytes: int = 100 * 1024) -> str:
        """
        Cria preview truncado do conteúdo do arquivo.
        Retorna primeiras max_lines linhas ou primeiros max_bytes, o que for menor.
        """
        try:
            # Decodificar para string
            text = file_bytes.decode("utf-8", errors="replace")
            lines = text.split("\n")

            # Limitar por linhas
            preview_lines = lines[:max_lines]

            # Limitar por bytes
            preview_text = "\n".join(preview_lines)
            if len(preview_text.encode("utf-8")) > max_bytes:
                # Truncar por bytes mantendo linhas completas
                truncated = ""
                for line in preview_lines:
                    line_bytes = (truncated + line + "\n").encode("utf-8")
                    if len(line_bytes) > max_bytes:
                        break
                    truncated += line + "\n"
                preview_text = truncated.rstrip()
                if len(preview_text.encode("utf-8")) < len(file_bytes):
                    preview_text += "\n... (arquivo truncado)"
            else:
                if len(preview_lines) < len(lines):
                    preview_text += "\n... (arquivo truncado)"

            return preview_text

        except Exception as e:
            logger.warning(f"DiscordService: falha ao criar preview: {e}")
            return f"[Erro ao processar preview: {str(e)}]"

    def _send_embed(self, title: str, description: str, color: int, fields: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Monta e envia o embed. Retorna True se status 204/200, False caso contrário.
        Silencioso se webhook não configurado.
        """
        if not self.webhook_url:
            # Não quebra o app — apenas loga localmente
            logger.debug("DiscordService: webhook não configurado — ignorando envio.")
            return False

        embed = {
            "title": title or "",
            "description": description or "",
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {"text": self.footer_text},
        }

        if fields:
            # Discord aceita até 25 fields por embed
            embed["fields"] = fields[:25]

        payload = {
            "username": self.username,
            "embeds": [embed],
        }

        headers = {"Content-Type": "application/json"}

        try:
            if requests:
                resp = requests.post(self.webhook_url, json=payload, headers=headers, timeout=5)
                if resp.status_code in (200, 204):
                    return True
                else:
                    logger.warning(f"DiscordService: webhook retornou {resp.status_code} - {resp.text}")
                    if resp.status_code == 429:
                        logger.warning("DiscordService: rate limited (429).")
                    return False
            else:
                # urllib fallback
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(self.webhook_url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    # sucesso normalmente 204 No Content
                    status = getattr(resp, "status", None) or getattr(resp, "getcode", lambda: None)()
                    if status in (200, 204):
                        return True
                    logger.warning(f"DiscordService: webhook retornou {status}")
                    return False
        except Exception as e:
            # Não crashar a aplicação. Loga o erro localmente.
            logger.exception("DiscordService: falha ao enviar webhook para Discord: %s", e)
            return False
