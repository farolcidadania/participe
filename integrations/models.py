from __future__ import annotations

import base64
import hashlib
import io
from django.db import models
from django.conf import settings

try:
    from cryptography.fernet import Fernet
    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False


def _get_fernet() -> "Fernet":
    """
    Deriva uma chave Fernet de 32 bytes a partir do SECRET_KEY do Django.
    Usa SHA-256 para normalizar o tamanho antes de codificar em URL-safe base64.
    """
    if not _FERNET_AVAILABLE:
        raise RuntimeError(
            "Biblioteca 'cryptography' não instalada. "
            "Execute: pip install cryptography"
        )
    key_bytes = settings.SECRET_KEY.encode("utf-8")
    digest = hashlib.sha256(key_bytes).digest()          # sempre 32 bytes
    fernet_key = base64.urlsafe_b64encode(digest)        # Fernet exige base64 url-safe
    return Fernet(fernet_key)



class CamaraToken(models.Model):
    nome = models.CharField(max_length=100)
    token = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class DiscordWebhook(models.Model):
    url = models.URLField(
        max_length=255, 
        verbose_name="URL do Webhook",
        help_text="URL completa do webhook do Discord"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo"
    )
    dev = models.BooleanField(
        default=False,
        verbose_name="Desenvolvimento"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Webhook do Discord"
        verbose_name_plural = "Webhooks do Discord"

    def __str__(self):
        return f"Webhook {self.pk} - {'Ativo' if self.is_active else 'Inativo'}"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Verifica se já existe outro webhook ativo com o mesmo tipo (dev ou não)
            conflito = DiscordWebhook.objects.filter(
                is_active=True,
                dev=self.dev,
            ).exclude(pk=self.pk)

            if conflito.exists():
                tipo = "dev" if self.dev else "social"
                raise ValueError(
                    f"Já existe um webhook - '{tipo}'. "
                    "Desative o existente antes de ativar outro."
                )

        return super().save(*args, **kwargs)


class GoogleSheetsConfig(models.Model):
    """
    Configuração da integração com o Google Sheets.
    Apenas uma configuração pode estar ativa por vez.

    O arquivo de credenciais é armazenado criptografado em disco (Fernet/AES-128-CBC)
    usando uma chave derivada do SECRET_KEY do Django.
    Use `get_decrypted_credentials()` para obter o conteúdo JSON em memória.
    """
    credentials = models.FileField(
        upload_to='files/credentials',
        verbose_name="Credenciais (JSON)",
        help_text="Arquivo JSON da Service Account do Google. Armazenado criptografado.",
    )
    spreadsheet_name = models.CharField(
        max_length=255,
        verbose_name="Nome da Planilha",
        help_text="Nome exato da planilha no Google Drive.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Ativo",
    )
    worksheet_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nome da tabela",
        help_text="Nome exato da tabela no Google Sheets.",
    )

    class Meta:
        verbose_name = "Configuração do Google Sheets"
        verbose_name_plural = "Configurações do Google Sheets"

    def __str__(self):
        status = "Ativa" if self.is_active else "Inativa"
        return f"{self.spreadsheet_name} [{status}]"

    # ------------------------------------------------------------------ #
    # Criptografia                                                         #
    # ------------------------------------------------------------------ #

    def save(self, *args, **kwargs):
        """Valida unicidade e criptografa o arquivo de credenciais antes de persistir."""
        if self.is_active:
            conflito = GoogleSheetsConfig.objects.filter(
                is_active=True,
            ).exclude(pk=self.pk)
            if conflito.exists():
                raise ValueError(
                    "Já existe uma configuração do Google Sheets ativa. "
                    "Desative a existente antes de ativar outra."
                )

        # Criptografa o arquivo se for um upload novo (InMemoryUploadedFile / TemporaryUploadedFile)
        if self.credentials and hasattr(self.credentials.file, 'read'):
            raw = self.credentials.file.read()
            # Evita re-criptografar arquivos já criptografados (salvos anteriormente)
            if not self._is_encrypted(raw):
                encrypted = _get_fernet().encrypt(raw)
                # Reescreve o buffer em memória com o conteúdo cifrado
                self.credentials.file = io.BytesIO(encrypted)
                self.credentials.file.seek(0)
                # Atualiza o tamanho reportado pelo campo para evitar erros de storage
                if hasattr(self.credentials, 'size'):
                    self.credentials.size = len(encrypted)

        return super().save(*args, **kwargs)

    def get_decrypted_credentials(self) -> dict:
        """
        Lê e descriptografa o arquivo de credenciais em memória.

        Returns:
            dict com o conteúdo JSON da Service Account.

        Raises:
            RuntimeError se a descriptografia falhar ou o arquivo não existir.
        """
        import json
        if not self.credentials:
            raise RuntimeError("Nenhum arquivo de credenciais configurado.")
        try:
            self.credentials.open('rb')
            raw = self.credentials.read()
            self.credentials.close()
        except Exception as e:
            raise RuntimeError(f"Falha ao ler arquivo de credenciais: {e}") from e

        try:
            plaintext = _get_fernet().decrypt(raw)
        except Exception as e:
            raise RuntimeError(
                "Falha ao descriptografar credenciais. "
                "Verifique se o SECRET_KEY não foi alterado desde o upload."
            ) from e

        try:
            return json.loads(plaintext.decode("utf-8"))
        except Exception as e:
            raise RuntimeError(f"Credenciais descriptografadas não são um JSON válido: {e}") from e

    @staticmethod
    def _is_encrypted(data: bytes) -> bool:
        """
        Heurística leve: tokens Fernet começam com 'gAAA' em base64 url-safe.
        Evita dupla criptografia ao re-salvar a instância sem novo upload.
        """
        try:
            return data.startswith(b'gAAA')
        except Exception:
            return False
  

class APIKeys(models.Model):
    SERVICE_CHOICES = [
        ('openai', 'OpenAI'),
        ('gemini', 'Gemini'),
    ]
    nome = models.CharField(max_length=100)
    api_key = models.CharField(max_length=255) # cryptography.fernet
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Chave de API"
        verbose_name_plural = "Chaves de API"

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if self.is_default:
            # Verifica se já existe outro provedor definido como padrão
            conflito = APIKeys.objects.filter(is_default=True).exclude(pk=self.pk)
            if conflito.exists():
                raise ValueError(
                    "Já existe uma chave de API definida como padrão (is_default). "
                    "Desmarque o padrão existente antes de ativar outra."
                )

        """Criptografa a api_key antes de persistir no banco de dados."""
        if self.api_key and not self._is_encrypted(self.api_key):
            raw = self.api_key.encode("utf-8")
            encrypted = _get_fernet().encrypt(raw)
            self.api_key = encrypted.decode("utf-8")
        
        return super().save(*args, **kwargs)

    def get_decrypted_api_key(self) -> str:
        """
        Descriptografa e retorna a api_key.

        Returns:
            str com a api_key original.

        Raises:
            RuntimeError se a descriptografia falhar ou a chave não existir.
        """
        if not self.api_key:
            raise RuntimeError("Nenhuma api_key configurada.")
        
        if not self._is_encrypted(self.api_key):
            return self.api_key

        try:
            encrypted_bytes = self.api_key.encode("utf-8")
            plaintext = _get_fernet().decrypt(encrypted_bytes)
            return plaintext.decode("utf-8")
        except Exception as e:
            raise RuntimeError(
                "Falha ao descriptografar a api_key. "
                "Verifique se o SECRET_KEY não foi alterado."
            ) from e

    @staticmethod
    def _is_encrypted(data: str) -> bool:
        """
        Heurística leve: tokens Fernet começam com 'gAAA' em base64 url-safe.
        Evita dupla criptografia ao re-salvar a instância.
        """
        return data.startswith("gAAA")


class AIUsage(models.Model):
    from_api = models.ForeignKey(APIKeys, on_delete=models.CASCADE, related_name="ai_usage")
    messages = models.JSONField(default=list)
    response = models.JSONField(default=list)
    tokens_prompt = models.IntegerField(default=0)
    tokens_response = models.IntegerField(default=0)
    tokens_total = models.IntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Uso de IA"
        verbose_name_plural = "Usos de IA"

    def __str__(self):
        return f"Uso de IA - {self.timestamp}"