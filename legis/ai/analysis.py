import os
import csv
import json
import logging
from integrations.services.providers_ai import AIProvidersService

logger = logging.getLogger(__name__)

class AIAnalise:
    def __init__(self):
        try:
            self.ai = AIProvidersService()
        except ValueError as e:
            logger.warning(f"Integração com IA desabilitada: {e}")
            self.ai = None

        # Define o caminho para o arquivo no diretório scraper
        base_dir = os.path.dirname(os.path.abspath(__file__))
        MEMORIA_PATH = os.path.join(base_dir, "data", "memoria_classificacoes.csv")

        self.memoria_contexto = []
        self.exemplos_otimizados = ""

        # carrega UMA vez só (evita leitura repetida do disco)
        try:
            with open(MEMORIA_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                exemplos_por_assunto = {}
                
                for row in reader:
                    ementa = row.get("Ementa", "").strip()
                    assunto = row.get("Assunto", "").strip()
                    
                    if ementa and assunto:
                        self.memoria_contexto.append({
                            "Ementa": ementa,
                            "Assunto": assunto
                        })
                        
                        # Pegamos no máximo 2 exemplos por assunto para não estourar os tokens
                        if assunto not in exemplos_por_assunto:
                            exemplos_por_assunto[assunto] = []
                        if len(exemplos_por_assunto[assunto]) < 2:
                            exemplos_por_assunto[assunto].append(ementa)

            # Monta a string otimizada de exemplos uma única vez
            linhas_exemplos = []
            for ass, ementas in exemplos_por_assunto.items():
                for em in ementas:
                    linhas_exemplos.append(f"Ementa: {em}\nAssunto: {ass}")
            
            self.exemplos_otimizados = "\n\n".join(linhas_exemplos)

            logger.info(f"Memória contextual carregada: {len(self.memoria_contexto)} totais, {len(linhas_exemplos)} amostras no prompt.")
        except Exception as e:
            logger.warning(f"Memória IA não carregada: {e}")

    def analise(self, message):
        if not self.ai:
            return {"Assunto": None, "Tema": None}
            
        logger.info("Analisando mensagem...")
        
        assuntos_txt = "\n".join(f"- {a}" for a in ASSUNTOS_VALIDOS)

        prompt = f"""
Você é uma assistente de classificação legislativa do projeto Farol da Cidadania.

Use os exemplos reais abaixo como referência de decisão.

EXEMPLOS JÁ CLASSIFICADOS:
{self.exemplos_otimizados}

Classifique usando APENAS um dos assuntos permitidos:

{assuntos_txt}

Retorne SOMENTE JSON válido:

{{
"Assunto": "nome do assunto"
}}

Descrição:
\"\"\"{message}\"\"\"
"""
        try:
            content = self.ai.execute_prompt(prompt)
            try:
                analise_dict = json.loads(content)
            except json.JSONDecodeError:
                analise_dict = {"Assunto": "Outros"}
                
            assunto = analise_dict.get("Assunto", "Outros")
            analise_dict["Tema"] = ASSUNTO_PARA_TEMA.get(assunto, "Outros")
            
            return analise_dict
        except Exception as e:
            logger.error(f"Erro na análise: {e}")
            return {"Assunto": "Erro", "Tema": "Erro"}


# --- MAPEAMENTO DE ASSUNTOS -> TEMAS ---
ASSUNTO_PARA_TEMA_GRUPO = {
    "Atividades Administrativas": [
        "Arquivamento de proposição", "Desarquivamento de proposição", "Juntada de documento",
        "Emenda", "Pedido de reconsideração", "Recurso Regimental", "Substituição de vereador", "Solicitação de urgência"],
    "Criação de frente parlamentar": ["Frente Parlamentar"],
    "Criação de bloco parlamentar": ["Bloco Parlamentar"],
    "Homenagens e Títulos": [
        "Medalha Antonieta de Barros", "Medalha Beata Joana de Gusmão", "Medalha Cruz e Sousa", "Medalha Divino Espírito Santo", "Medalha do Mérito Desportivo Miguel Livramento",
        "Medalha Francisco Dias Velho", "Medalha Herbert de Souza", "Medalha Jennifer Celia Henrique", "Medalha João Paulo II", "Medalha Manezinho da Ilha Aldírio Simões",
        "Medalha Professor João David Ferreira Lima", "Medalha Virgílio Várzea", "Sessão Comemorativa", "Sessão Solene", "Título de cidadã e cidadão honorário",
        "Título de utilidade pública", "Troféu Vereador Pedro Medeiros", "Troféu Erotides Helena da Silva", "Troféu Governador Celso Ramos",
        "Uso do Grande Expediente para homenagem"],
    "Moção": ["Moção de aplausos", "Moção de protesto", "Moção de repúdio"],
    "Datas comemorativas e dias de conscientização": ["Dia Municipal", "Mês Municipal", "Semana Municipal"],
    "Legalização e denominação de espaços públicos": ["Denominação de espaço público", "Denominação de via pública", "Legalização de via pública"],
    "Administração Pública": [
        "Gestão de pessoas e carreira no serviço público", "Compras, contratos e patrimônio público",
        "Relações institucionais e cooperação", "Alvarás e liberações administrativas", "Planejamento e orçamento público",
        "Atendimento ao cidadão e serviços públicos essenciais", "Organização administrativa e estrutura governamental",
        "Fiscalização administrativa e sanções"],
    "Cultura, Esporte e Lazer": [
        "Apoio e fomento ao esporte", "Criação e manutenção de área de lazer e atividade física", "Evento cultural",
        "Gestão e Regulação da Cultura e Lazer", "Patrimônio cultural", "Regulação e fomento ao turismo"],
    "Direitos dos Animais": ["Bem-estar e proteção animal", "Gestão da política de proteção animal"],
    "Direitos Humanos, Igualdade Social e Assistência Social": [
        "Acessibilidade", "Direitos de crianças e adolescentes","Diversidade sexual e de gênero",
        "Gestão de Políticas Sociais, de Direitos e Equidade", "Moradia","Pessoas com deficiência e neurodivergentes",
        "Pessoas em vulnerabilidade ou risco social", "Promoção da equidade e combate à discriminação", "Política para mulheres",
        "Povos Tradicionais", "Rede de Assistência Social","Segurança alimentar e nutricional"],
    "Educação": [
        "Ampliação da rede física escolar", "Aquisição de equipamentos e mobiliário escolar", "Currículo escolar",
        "Educação de jovens e adultos (eja)", "Gestão da Política Educacional", "Manutenção da estrutura escolar",
        "Material didático", "Terceirização de serviço", "Trabalhadores da educação", "Vagas em creches e escolas"],
    "Mobilidade Urbana": [
        "Estacionamentos e vagas rotativas", "Expansão da infraestrutura de mobilidade", "Gestão e Regulação da Mobilidade Urbana",
        "Infraestrutura cicloviária", "Manutenção da infraestrutura viária", "Manutenção de pontos de ônibus",
        "Organização do trânsito", "Serviços de transporte individual privado", "Transporte público"],
    "Políticas de Trabalho e Renda": ["Direitos e condições de trabalho", "Promoção do trabalho e da renda"],
    "Políticas de zoneamento e uso do solo": [
        "Legalização e denominação de vias e espaços públicos", "Impactos urbanísticos de empreendimentos",
        "Moradia", "Plano diretor", "Perímetro urbano e delimitações", "Regularização fundiária", "Zoneamento"],
    "Postura, Moral e Costumes": ["Poluição sonora", "Decoro e conduta em espaços públicos"],
    "Saneamento": [
        "Rede de esgotamento sanitário", "Gestão e Regulação dos Serviços de Saneamento",
        "Rede de drenagem", "Rede de abastecimento de água"],
    "Saúde": [
        "Controle sanitário e vigilância em saúde", "Diversidade sexual e de gênero", "Equipamentos públicos de saúde",
        "Gestão e Regulação da Saúde Pública", "Pessoas com deficiência e neurodivergentes", "Prevenção e combate de doenças",
        "Rede de Atenção Psicossocial (RAPS)", "Trabalhadores da saúde"],
    "Segurança Pública": [
        "Gestão e Regulação da Segurança Pública", "Infraestrutura de segurança", "Prevenção e policiamento", "Segurança e monitoramento de espaços públicos",
        "Segurança nas escolas e entorno escolar", "Violência e criminalidade urbana", "Violência do Estado"],
    "Sustentabilidade": [
        "Áreas protegidas e conservação ambiental", "Educação ambiental", "Energia e sustentabilidade",
        "Gestão de resíduos", "Gestão e proteção de corpos hídricos e áreas associadas", "Governança ambiental",
        "Instrumentos de regulação e controle ambiental", "Mudanças climáticas", "Vegetação e arborização urbana"],
    "Zeladoria Urbana": [
        "Limpeza Urbana", "Manutenção de rede elétrica", "Iluminação pública", "Gestão e Regulação da Zeladoria Urbana", "Obras e Reparos Urbanos"],
}
ASSUNTO_PARA_TEMA = {assunto: tema for tema, lista in ASSUNTO_PARA_TEMA_GRUPO.items() for assunto in lista}
ASSUNTOS_VALIDOS = sorted(list(ASSUNTO_PARA_TEMA.keys()))
