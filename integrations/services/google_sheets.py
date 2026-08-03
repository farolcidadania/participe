from __future__ import annotations

import os
import time
from typing import Optional, List, Any

import logging
from django.conf import settings
from ..models import GoogleSheetsConfig

logger = logging.getLogger(__name__)
from integrations.services.discord import DiscordService
import gspread
from django.utils import timezone

from google.oauth2.service_account import Credentials

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

discord = DiscordService(username="SheetsService", dev=True)


class SheetsService:
    """
    Serviço para sincronizar dados com uma planilha Google Sheets.

    Lê a configuração de:
      - Model GoogleSheetsConfig (banco de dados)
      - settings.GOOGLE_SHEETS_CREDENTIALS_PATH (fallback)
      - settings.GOOGLE_SHEETS_SPREADSHEET_NAME (fallback)

    Métodos públicos:
      - append_row(worksheet_name, row)
      - update_row(worksheet_name, row_index, row)
      - find_and_update_row(worksheet_name, search_col, search_value, row)
      - get_all_rows(worksheet_name)
      - clear_and_write(worksheet_name, rows)
    """

    def __init__(self):
        self.client: Optional[Any] = None
        self.spreadsheet_name: Optional[str] = None
        self.worksheet_name: Optional[str] = None
        self._spreadsheet: Optional[Any] = None
        self.worksheet_name: Optional[str] = None
        
        if not gspread or not Credentials:
            logger.warning(
                "biblioteca 'gspread' ou 'google-auth' não instalada — "
                "operações no Google Sheets serão ignoradas."
            )
            return

        creds_dict: Optional[dict] = None

        # 1. Tenta buscar configuração criptografada no banco
        try:
            config = GoogleSheetsConfig.objects.filter(is_active=True).first()
            if config:
                self.spreadsheet_name = config.spreadsheet_name
                self.worksheet_name = getattr(config, 'worksheet_name', None)
                creds_dict = config.get_decrypted_credentials()
            else:
                logger.error(
                    "nenhuma GoogleSheetsConfig ativa encontrada no banco. "
                    "Cadastre uma configuração no admin antes de rodar a fila."
                )
        except Exception as exc:
            # Exibe como ERROR para aparecer visível no terminal do fila.bat
            logger.error(
                "falha ao carregar configuração do banco — %s. "
                "Verifique se a migrate foi aplicada e se o banco está acessível.",
                exc,
            )

        # 2. Fallback para settings (caminho de arquivo em texto puro, sem criptografia)
        if not self.spreadsheet_name:
            self.spreadsheet_name = getattr(settings, "GOOGLE_SHEETS_SPREADSHEET_NAME", None)
            if self.spreadsheet_name:
                logger.info(
                    "usando planilha do settings: '%s'.", self.spreadsheet_name
                )
        if not self.worksheet_name:
            self.worksheet_name = getattr(settings, "GOOGLE_SHEETS_WORKSHEET_NAME", None)
        if creds_dict is None:
            fallback_path = getattr(settings, "GOOGLE_SHEETS_CREDENTIALS_PATH", None)
            if fallback_path:
                try:
                    import json
                    with open(fallback_path, "r", encoding="utf-8") as f:
                        creds_dict = json.load(f)
                    logger.info("credenciais carregadas do fallback: %s", fallback_path)
                except Exception as exc:
                    logger.error(
                        "SheetsService: falha ao ler credenciais do fallback '%s': %s",
                        fallback_path, exc,
                    )

        if not creds_dict or not self.spreadsheet_name:
            logger.error(
                "inicialização incompleta — credenciais=%s | planilha=%s. "
                "Operações no Google Sheets serão ignoradas. "
                "Cadastre uma GoogleSheetsConfig ativa no admin (/admin/).",
                'OK' if creds_dict else 'AUSENTE',
                self.spreadsheet_name or 'AUSENTE',
            )
            return

        try:
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            self.client = gspread.authorize(creds)
        except Exception as e:
            logger.exception("falha na autenticação: %s", e)

    def _execute_with_retry(self, action, error_context, fallback=False):
        """
        Executa uma ação com retentativa em caso de erro de rate limit (429).
        """
        for attempt in range(2):
            try:
                return action()
            except gspread.exceptions.APIError as e:
                if (hasattr(e, 'response') and e.response.status_code == 429) or '429' in str(e):
                    if attempt == 0:
                        logger.warning("Limite de API atingido (429). Aguardando 30s...")
                        time.sleep(30)
                        continue
                logger.exception("erro de API %s: %s", error_context, e)
                return fallback
            except Exception as e:
                logger.exception("erro %s: %s", error_context, e)
                return fallback
        return fallback

    # ------------------------------------------------------------------ #
    # Métodos públicos                                                     #
    # ------------------------------------------------------------------ #

    def append_row(self, row: List[Any], worksheet_name: Optional[str] = None) -> bool:
        """
        Adiciona uma linha ao final da aba configurada (ou especificada).

        Args:
            row: Lista de valores a serem inseridos.
            worksheet_name: Nome da aba (opcional). Se None, usa a aba configurada.

        Returns:
            True se bem-sucedido, False caso contrário.
        """
        target_worksheet = worksheet_name or self.worksheet_name
        if not target_worksheet:
            logger.error("nenhum worksheet_name definido.")
            return False

        aba = self._get_worksheet(target_worksheet)
        if aba is None:
            return False
            
        def action():
            aba.append_row(row, value_input_option="USER_ENTERED")
            return True

        return self._execute_with_retry(
            action, 
            f"ao adicionar linha na aba '{target_worksheet}'", 
            fallback=False
        )

    def update_row(self, row_index: int, row: List[Any], worksheet_name: Optional[str] = None) -> bool:
        """
        Sobrescreve a linha em `row_index` (1-based) na aba configurada (ou especificada).

        Args:
            row_index: Índice da linha (começa em 1).
            row: Lista de valores a serem escritos.
            worksheet_name: Nome da aba (opcional).

        Returns:
            True se bem-sucedido, False caso contrário.
        """
        target_worksheet = worksheet_name or self.worksheet_name
        if not target_worksheet:
            logger.error("nenhum worksheet_name definido.")
            return False

        aba = self._get_worksheet(target_worksheet)
        if aba is None:
            return False
            
        col_end = self._col_letter(len(row))
        cell_range = f"A{row_index}:{col_end}{row_index}"
        
        def action():
            aba.update(cell_range, [row], value_input_option="USER_ENTERED")
            logger.info("linha %d atualizada na aba '%s'.", row_index, target_worksheet)
            return True

        return self._execute_with_retry(
            action, 
            f"ao atualizar linha {row_index} na aba '{target_worksheet}'", 
            fallback=False
        )

    def find_and_update_row(
        self,
        search_col: int,
        search_value: str,
        row: List[Any],
        worksheet_name: Optional[str] = None,
    ) -> bool:
        """
        Localiza a primeira linha onde `search_col` (1-based) == `search_value`
        e a substitui pelos valores de `row`.

        Args:
            search_col: Número da coluna para busca (1-based).
            search_value: Valor a ser buscado.
            row: Novos valores para a linha encontrada.
            worksheet_name: Nome da aba (opcional).

        Returns:
            True se encontrou e atualizou, False caso contrário.
        """
        target_worksheet = worksheet_name or self.worksheet_name
        if not target_worksheet:
            logger.error("nenhum worksheet_name definido.")
            return False

        aba = self._get_worksheet(target_worksheet)
        if aba is None:
            return False
            
        def find_action():
            try:
                return aba.find(str(search_value), in_column=search_col)
            except gspread.exceptions.CellNotFound:
                return None
                
        cell = self._execute_with_retry(
            find_action, 
            f"ao buscar na aba '{target_worksheet}'", 
            fallback=None
        )
                
        if cell is None:
            # col_letter = self._col_letter(search_col)
            # logger.info(
            #     "valor '%s' não encontrado na coluna %s da aba '%s'.",
            #     search_value, col_letter, target_worksheet,
            # )
            return False
            
        return self.update_row(cell.row, row, target_worksheet)

    def patch_row(self, row_index: int, col_values: dict, worksheet_name: Optional[str] = None) -> bool:
        """
        Atualiza apenas as colunas especificadas de uma linha.
        
        Args:
            row_index: Índice da linha (começa em 1).
            col_values: Dicionário onde a chave é o índice da -based) e o valor é o dado a ser escrito.
            worksheet_name: Nome da aba (opcional).
            
        Returns:
            True se bem-sucedido, False caso contrário.
        """
        target_worksheet = worksheet_name or self.worksheet_name
        if not target_worksheet:
            logger.error("nenhum worksheet_name definido.")
            return False

        aba = self._get_worksheet(target_worksheet)
        if aba is None:
            return False
            
        data = []
        for col_index, val in col_values.items():
            col_letter = self._col_letter(col_index)
            cell_range = f"{col_letter}{row_index}"
            data.append({'range': cell_range, 'values': [[val]]})
            
        def action():
            aba.batch_update(data, value_input_option="USER_ENTERED")
            return True

        return self._execute_with_retry(
            action, 
            f"ao fazer patch na linha {row_index} na aba '{target_worksheet}'", 
            fallback=False
        )

    def find_and_patch_row(
        self,
        search_col: int,
        search_value: str,
        col_values: dict,
        worksheet_name: Optional[str] = None,
    ) -> bool:
        """
        Localiza a primeira linha onde `search_col` (1-based) == `search_value`
        e atualiza apenas as colunas especificadas em `col_values`.

        Args:
            search_col: Número da coluna para busca (1-based).
            search_value: Valor a ser buscado.
            col_values: Dicionário onde a chave é o índice da coluna (1-based) e o valor é o novo dado.
            worksheet_name: Nome da aba (opcional).

        Returns:
            True se encontrou e atualizou, False caso contrário.
        """
        target_worksheet = worksheet_name or self.worksheet_name
        if not target_worksheet:
            logger.error("nenhum worksheet_name definido.")
            return False

        aba = self._get_worksheet(target_worksheet)
        if aba is None:
            return False
            
        def find_action():
            try:
                return aba.find(str(search_value), in_column=search_col)
            except gspread.exceptions.CellNotFound:
                return None
                
        cell = self._execute_with_retry(
            find_action, 
            f"ao buscar na aba '{target_worksheet}'", 
            fallback=None
        )
                
        if cell is None:
            # col_letter = self._col_letter(search_col)
            # logger.info(
            #     "valor '%s' não encontrado na coluna %s da aba '%s'.",
            #     search_value, col_letter, target_worksheet,
            # )
            return False
            
        return self.patch_row(cell.row, col_values, target_worksheet)

    def get_all_rows(self, worksheet_name: Optional[str] = None) -> Optional[List[List[Any]]]:
        """
        Retorna todas as linhas da aba como lista de listas.

        Args:
            worksheet_name: Nome da aba (opcional).

        Returns:
            Lista de linhas, ou None em caso de erro.
        """
        target_worksheet = worksheet_name or self.worksheet_name
        if not target_worksheet:
            logger.error("nenhum worksheet_name definido.")
            return None

        aba = self._get_worksheet(target_worksheet)
        if aba is None:
            return None
        try:
            rows = aba.get_all_values()
            logger.debug(
                "%d linhas lidas da aba '%s'.", len(rows), target_worksheet
            )
            return rows
        except Exception as e:
            logger.exception(
                "erro ao ler linhas da aba '%s': %s", target_worksheet, e
            )
            return None

    def clear_and_write(self, rows: List[List[Any]], worksheet_name: Optional[str] = None) -> bool:
        """
        Limpa a aba e escreve todas as linhas de uma vez (substituição total).
        Útil para sincronização completa da planilha.

        Args:
            rows: Lista de listas representando todas as linhas.
            worksheet_name: Nome da aba (opcional).

        Returns:
            True se bem-sucedido, False caso contrário.
        """
        target_worksheet = worksheet_name or self.worksheet_name
        if not target_worksheet:
            logger.error("nenhum worksheet_name definido.")
            return False

        aba = self._get_worksheet(target_worksheet)
        if aba is None:
            return False
        try:
            aba.clear()
            if rows:
                aba.update("A1", rows, value_input_option="USER_ENTERED")
            logger.info(
                "aba '%s' reescrita com %d linhas.", target_worksheet, len(rows)
            )
            return True
        except Exception as e:
            logger.exception(
                "erro ao reescrever aba '%s': %s", target_worksheet, e
            )
            return False

    # ------------------------------------------------------------------ #
    # Métodos privados                                                     #
    # ------------------------------------------------------------------ #

    def _get_spreadsheet(self) -> Optional[Any]:
        """Abre (e cacheia) a planilha configurada."""
        if not self.client:
            return None
        if self._spreadsheet is None:
            try:
                self._spreadsheet = self.client.open(self.spreadsheet_name)
            except Exception as e:
                logger.exception(
                    "não foi possível abrir a planilha '%s': %s",
                    self.spreadsheet_name, e,
                )
                return None
        return self._spreadsheet

    def _get_worksheet(self, name: str) -> Optional[Any]:
        """Retorna a aba pelo nome. Loga erro se não encontrada."""
        sh = self._get_spreadsheet()
        if sh is None:
            return None
        try:
            return sh.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            # logger.warning(
            #     "aba '%s' não encontrada na planilha '%s'.",
            #     name, self.spreadsheet_name,
            # )
            return None
        except Exception as e:
            logger.exception(
                "erro ao acessar aba '%s': %s", name, e
            )
            return None

    @staticmethod
    def _col_letter(col_index: int) -> str:
        """Converte índice de coluna (1-based) para letra(s), ex: 1→A, 26→Z, 27→AA."""
        result = ""
        while col_index > 0:
            col_index, remainder = divmod(col_index - 1, 26)
            result = chr(65 + remainder) + result
        return result


class MateriasSheetService:
    def __init__(self, instance):
        self.now = timezone.localtime() 
        self.instance = instance
        self.service = SheetsService()

        if not self.service.client:
            discord.log_danger(
                "[Sheets] Falha de conexão: SheetsService sem cliente autenticado. "
                "Verifique se há uma GoogleSheetsConfig ativa com credenciais válidas "
                "(planilha: '%s'). Matéria #%s NÃO foi enviada.",
                self.service.spreadsheet_name or 'não configurada',
                instance.id,
            )
            return

        
    
    def sync(self):
        try:
            logger.info(f"Iniciando sincronização google sheets - {self.instance.get_number_p_date}")
            # Primeiro, tentar atualizar apenas as colunas necessárias:
            # A (1) = Última atualização
            # G (7) = Situação
            col_values_to_update = {
                1: self.now.strftime('%d/%m/%Y %H:%M:%S'),
                7: self.instance.tramitacoes.last().situacao if self.instance.tramitacoes.last() else '',
            }        
            success = self.service.find_and_patch_row(
                search_col=9, # I (9) = Nº da Matéria
                search_value=self.instance.get_number_p_date,
                col_values=col_values_to_update
            )
            

            if not success:
                autores_list = [a.nome for a in self.instance.autores.all()]
                autor_principal = autores_list[0] if len(autores_list) > 0 else ''
                autor_2 = autores_list[1] if len(autores_list) > 1 else ''
                autor_3 = autores_list[2] if len(autores_list) > 2 else ''
                autor_4 = autores_list[3] if len(autores_list) > 3 else ''
                autor_5 = autores_list[4] if len(autores_list) > 4 else ''

                row = [
                    self.now.strftime('%d/%m/%Y %H:%M:%S'), # A: Última atualização
                    '', # B: Responsável
                    '', # C: Revisor 
                    self.instance.link_externo or '', # D: Link
                    '', # E: Mês 
                    self.instance.data_apresentacao.strftime('%d/%m/%Y') if self.instance.data_apresentacao else '', # F: Data
                    self.instance.tramitacoes.last().situacao if self.instance.tramitacoes.last() else '', # G: Situação
                    self.instance.get_tipo_display, # H: Tipo
                    self.instance.get_number_p_date, # I: Nº
                    autor_principal, # J: Autoria
                    self.instance.get_partido_materia, # K: Partido
                    autor_2, # L: Autoria 2
                    autor_3, # M: Autoria 3
                    autor_4, # N: Autoria 4
                    autor_5, # O: Autoria 5
                    self.instance.ementa, # P: Ementa
                    self.instance.get_regiao_display, # Q: Região
                    self.instance.tema_by_ia or '', # R: Tema
                    self.instance.assunto_by_ia or '', # S: Assunto
                    self.instance.palavras_chaves or '', # T: Palavras chaves
                    self.instance.get_function, # U: Funções
                    self.instance.eixo or '', # V: Eixo
                    'TRUE' if self.instance.participacao_publica else 'FALSE', # W: Part. Pública
                    'TRUE' if self.instance.justifica_regiao else 'FALSE', # X: Justifica região (ou religiosa)
                    '', # Y: Observações gerais
                    self.instance.get_status_display or '', # Z: STATUS
                ]
                success = self.service.append_row(row)
                logger.info(f"Linha criada - {self.instance.get_number_p_date}")

            if success:
                # Usa update() para salvar sem disparar novamente o signal de post_save
                type(self.instance).objects.filter(pk=self.instance.pk).update(last_updated_sheet=self.now)
            else:
                discord.log_danger(
                    f"[Sheets] Falha de sincronização. Não foi possível inserir/atualizar a "
                    f"Matéria #{self.instance.get_number_p_date} (ID: {self.instance.id}) no Google Sheets."
                )

        except Exception as exc:
            discord.log_danger(
                f"[Sheets] Erro CRÍTICO ao sincronizar Matéria "
                f"#{self.instance.get_number_p_date} (ID: {self.instance.id}): {str(exc)}"
            )
            raise