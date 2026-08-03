import unicodedata


def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto)
                if unicodedata.category(c) != 'Mn')



# --- ASSUNTOS DE CAMADA DUPLA---
BIBLIOTECAS_ASSUNTOS = {
    "Juntada de documento": {
        "grupo1": {"anexar", "anexada", "anexado", "juntada", "juntado"},
        "grupo2": {"certidao", "documento"}
    },
    "Arquivamento de proposição": {
        "grupo1": {"plc", "projeto", "proposicao", "requerimento", "indicacao", "mocao"},
        "grupo2": {"arquivamento"}
    },
    "Desarquivamento de proposição": {
        "grupo1": {"plc", "projeto", "projetos", "proposicao"},
        "grupo2": {"desarquivamento"}
    },
    "Solicitação de urgência": {
        "grupo1": {"solicita", "tramitacao"},
        "grupo2": {"urgencia"}
    },
    "Uso do Grande Expediente para homenagem": {
        "grupo1": {"grande expediente"},
        "grupo2": {"homenagem", "homenagear", "uso", "utilizacao"}
    },
    "Medalha Antonieta de Barros": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"antonieta de barros"}
    },
    "Medalha Beata Joana de Gusmão": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"beata joana de gusmao"}
    },
    "Medalha Cruz e Sousa": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"cruz e sousa"}
    },
    "Medalha Divino Espírito Santo": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"divino espirito santo"}
    },
    "Medalha do Mérito Desportivo Miguel Livramento": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"merito desportivo miguel livramento"}
    },
    "Medalha Francisco Dias Velho": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"francisco dias velho"}
    },
    "Medalha Herbert de Souza": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"herbert de souza"}
    },
    "Medalha Jennifer Celia Henrique": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"jennifer celia henrique"}
    },
    "Medalha João Paulo II": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"joao paulo ii"}
    },
    "Medalha Manezinho da Ilha Aldírio Simões": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"manezinho da ilha aldirio simoes"}
    },
    "Medalha Professor João David Ferreira Lima": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"professor joao david ferreira lima"}
    },
    "Medalha Virgílio Várzea": {
        "grupo1": {"medalha", "diploma"},
        "grupo2": {"virgilio varzea"}
    },
    "Manutenção de rede elétrica": {
        "grupo1": {"manutencao", "conserto", "reparo", "melhoria", "verificacao", "substituicao", "troca"},
        "grupo2": {"poste", "luminaria", "lampada", "rede eletrica", "fiacao", "transformador"}
    },
    "Aquisição de equipamentos e mobiliário escolar": {
        "grupo1": {"aquisicao", "compra", "substituicao"},
        "grupo2": {"ar-condicionado"}
    },
    "Gestão da Política Educacional":{
        "grupo1": {"rede municipal"},
        "grupo2": {"neim", "ebm", "escola"}
    },
    "Manutenção da estrutura escolar": {
        "grupo1": {"melhorias", "manutencao", "reparo", "condicoes estruturais", "reforma", "revitalizacao"},
        "grupo2": {"neim", "ebm", "escola"}
    },
    "Trabalhadores da educação": {
        "grupo1": {"lotacao de cargo", "nomeacao", "cargo", "concurso"},
        "grupo2": {"neim", "ebm", "escola", "secretaria municipal de educacao"}
    },
    "Expansão da infraestrutura de mobilidade": {
        "grupo1": {"expansao", "continuidade", "duplicacao"},
        "grupo2": {"avenida", "rua", "rodovia", "ponte", "passeio"}
    },
    "Manutenção da infraestrutura viária": {
        "grupo1": {"cobertura", "conserto", "construcao", "indicacao", "demandas", "instalacao", "manutencao", "melhoria", "obras",
                   "recapeamento", "recapear", "recolocacao", "recomposicao", "recuperacao", "relajotamento",
                   "reparo", "revitalizacao"},
        "grupo2": {"asfaltamento", "asfaltica", "asfaltico", "asfalto", "avenida", "buraco", "calcada", "calcamento",
                   "escadaria", "lajotas", "lombada", "passeio", "pavimentacao", "pavimento", "ponte", "rodovia",
                   "rotatoria", "servidao", "tachoes refletivos", "via", "viaduto", "viaria"}
    },
    "Manutenção de pontos de ônibus": {
        "grupo1": {"manutencao"},
        "grupo2": {"ponto de onibus", "abrigo de onibus"}
    },
    "Organização do trânsito": {
        "grupo1": {"instalacao", "recolocacao"},
        "grupo2": {"guard rail", "guarda corpo", "placa de identificacao"}
    },
    "Legalização e denominação de vias e espaços públicos": {
        "grupo1": {"denomina", "denominacao", "denominar"},
        "grupo2": {"via publica", "rua", "servidao", "logradouro", "parque", "praca", "creche"}
    },
    "Rede de abastecimento de água": {
        "grupo1": {"casan", "reparo", "reparar", "vazamento"},
        "grupo2": {"rede de agua", "abastecimento", "rede", "vazamento", "agua"}
    },
    "Prevenção e combate de doenças": {
        "grupo1": {"vacina", "vacinacao", "campanha"},
        "grupo2": {"covid-19", "covid", "gripe", "h1n1", "h3n2", "hpv"},
    },
    "Trabalhadores da saúde": {
        "grupo1": {"cs", "centro de saude", "posto de saude", "multihospital", "policlinica", "contratacao"},
        "grupo2": {"lotacao de cargo", "concurso", "profissional", "funcionarios", "medico", "enfermeiro", "farmaceutico", "odontologia"}
    },
    "Segurança nas escolas e entorno escolar": {
        "grupo1": {"seguranca", "camaras de seguranca", "camaras de monitoramento", "sistema de monitoramento"},
        "grupo2": {"neim", "ebm", "escola", "escolas", "educacao infantil", "rede municipal de ensino"}
    },
    "Iluminação pública": {
        "grupo1": {"substituicao", "troca"},
        "grupo2": {"lampada", "lampada queimada"}
    },
    "Limpeza Urbana": {
        "grupo1": {"remocao", "reparo", "retirada", "recolhimento", "limpeza", "poda", "instalacao"},
        "grupo2": {"arvore", "entulho", "lixo", "mato", "residuos", "resto de obra", "servidao",
                   "terreno", "vegetacao", "viaduto", "lixeira"}
    },
}

ASSUNTO_PARA_TEMA_GRUPO = {
    "Atividades Administrativas": [
        "Arquivamento de proposição", "Desarquivamento de proposição", "Juntada de documento",
        "Emenda", "Pedido de reconsideração", "Recurso Regimental", "Substituição de vereador", "Solicitação de urgência", "Substitutivo"],
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

# --- ASSUNTOS DIRETOS ---
ASSUNTOS_DIRETOS = {
    "Acessibilidade": {"rampa de acesso", "corrimao", "libras", "braile"},
    "Comissão Parlamentar de Inquérito": {"comissao parlamentar de inquerito"},
    "Comissão Parlamentar Especial": {"comissao parlamentar especial"},
    "Emenda": {"emenda"},
    "Pedido de reconsideração": {"pedido de reconsideracao"},
    "Reconstituição": {"reconstituicao"},
    "Recurso Regimental": {"recurso regimental"},
    "Substituição de vereador": {"substituicao de vereador"},
    "Substitutivo": {"substitutivo"},
    "Solicitação de urgência": {"solicitacao de urgencia"},
    "Frente Parlamentar": {"frente parlamentar"},
    "Bloco Parlamentar": {"bloco parlamentar"},
    "Medalha Antonieta de Barros": {"medalha antonieta de barros"},
    "Medalha Beata Joana de Gusmão": {"medalha beata joana de gusmao"},
    "Medalha Cruz e Sousa": {"medalha cruz e sousa"},
    "Medalha Divino Espírito Santo": {"medalha divino espirito santo"},
    "Medalha do Mérito Desportivo Miguel Livramento": {"medalha do merito desportivo miguel livramento", "medalha de merito desportivo miguel livramento"},
    "Medalha Francisco Dias Velho": {"medalha francisco dias velho"},
    "Medalha Herbert de Souza": {"medalha herbert de souza"},
    "Medalha Jennifer Celia Henrique": {"medalha jennifer celia henrique"},
    "Medalha João Paulo II": {"medalha joao paulo"},
    "Medalha Manezinho da Ilha Aldírio Simões": {"medalha manezinho da ilha aldirio simoes"},
    "Medalha Professor João David Ferreira Lima": {"medalha professor joao david ferreira lima"},
    "Medalha Virgílio Várzea": {"medalha virgilio varzea"},
    "Sessão Comemorativa": {"sessao comemorativa"},
    "Sessão Solene": {"sessao solene"},
    "Título de cidadã e cidadão honorário": {"titulo de cidadao", "titulo de cidada", "cidadao honorario", "cidada honoraria"},
    "Título de utilidade pública": {"titulo de utilidade publica", "utilidade publica"},
    "Troféu Vereador Pedro Medeiros": {"trofeu vereador pedro medeiros"},
    "Troféu Erotides Helena da Silva": {"trofeu erotides helena da silva"},
    "Troféu Governador Celso Ramos": {"trofeu governador celso ramos"},
    "Uso do Grande Expediente para homenagem": {"uso do grande expediente"},
    "Moção de aplausos": {"mocao de aplausos", "mocao de apoio"},
    "Moção de repúdio": {"mocao de repudio"},
    "Moção de protesto": {"mocao de protesto"},
    "Dia Municipal": {"dia municipal", "dia da conscientizacao", "dia de combate"},
    "Mês Municipal": {"mes municipal", "mes da conscientizacao", "mes de combate"},
    "Semana Municipal": {"semana municipal"},
    "Denominação de espaço público": {"denominacao do parque", "denomima praca", "denomimacao da praca"},
    "Denominação de via pública": {"denominacao de via publica"},
    "Legalização de via pública": {"legaliza via", "legaliza servidao", "legalizacao de via publica",
                                   "reconhecimento oficial da rua"},
    "Gestão de pessoas e carreira no serviço público": {"estatuto dos servidores", "regime proprio", "quadro de servidores", "alteracao da carreira", "estagios probatorios"},
    "Compras, contratos e patrimônio público": {"cessao de uso", "desafetacao de imovel", "alienacao de imovel"},
    "Relações institucionais e cooperação": {"acordo de cooperacao", "acordos de cooperacao"},
    "Alvarás e liberações administrativas": {"alvara", "alvaras"},
    "Planejamento e orçamento público": {"plano plurianual", "iptu", "iss", "lei orcamentaria anual", "loa"},
    "Atendimento ao cidadão e serviços públicos essenciais": {"pro-cidadao", "atendimento ao publico"},
    "Organização administrativa e estrutura governamental": {"reforma administrativa", "organizacao administrativa", "estrutura administrativa"},
    "Fiscalização administrativa e sanções": {"fiscalizacao administrativa", "inspecao administrativa", "multa", "sancao administrativa", "sancoes administrativas", "construcao irregular"},
    "Apoio e fomento ao esporte": {"onibus para atletas", "transporte para atletas", "competicao esportiva"},
    "Evento cultural": {"evento cultural", "carnaval", "pascoa solidaria", "berbigao do boca", "maratona cultural"},
    "Gestão e Regulação da Cultura e Lazer": {"fundacao cultural de florianopolis", "plano municipal de cultura",
                                              "politica nacional aldir blanc", "pnab", "conselho municipal de politica cultural",
                                              "fundo municipal de cultura", "comissao de educacão, cultura e desporto"},
    "Patrimônio cultural": {"patrimonio historico", "obras de arte", "obra de arte", "patrimonio cultural", "interesse historico", "sitio arqueologico"},
    "Regulação e fomento ao turismo": {"turismo"},
    "Bem-estar e proteção animal": {"vacinacao anti-cio", "castracao", "fiv e felv", "maus tratos", "leishmaniose", "animais domesticos"},
    "Gestão da política de proteção animal": {"fundo municipal de proteção e bem estar animal", "conselho de protecao animal", "samuvet"},
    "Direitos de crianças e adolescentes": {"conselho tutelar"},
    "Diversidade sexual e de gênero": {"parada do orgulho", "terapia de conversao", "orientacao sexual"},
    "Gestão de Políticas Sociais, de Direitos e Equidade": {"assistencia social"},
    "Moradia": {"minha casa, minha vida"},
    "Pessoas com deficiência e neurodivergentes": {"pcd", "autismo", "tea"},
    "Pessoas em vulnerabilidade ou risco social": {"internacao humanizada", "internacao compulsoria", "moradores de rua", "pessoas em situacao de rua",
                                                   "passarela da cidadania", "populacao em situacao de rua"},
    "Promoção da equidade e combate à discriminação": {"gratuitade no passe hiv+"},
    "Política para mulheres": {"servico de acolhimento a mulheres", "cremv", "feminicidio", "violencia contra mulheres"},
    "Povos Tradicionais": {"quilombola", "ribeirinho", "indigena"},
    "Rede de Assistência Social": {"cras", "centro de referência de assistencia social", "creas", "centro de referencia especializado de assistencia social",
                                   "acolhimento institucional", "comunidade terapeutica", "casa de passagem", "centro pop"},
    "Segurança alimentar e nutricional": {"restaurante popular", "cestas basicas"},
    "Violência do Estado": {"violencia policial", "violacao de direitos humanos"},
    "Ampliação da rede física escolar ": {"construcao de escola", "construcao da escola"},
    "Currículo escolar": {"curriculo escolar"},
    "Educação de jovens e adultos (eja)": {"educacao de jovens e adultos", "eja"},
    "Gestão da Política Educacional": {"escola em tempo integral", "assistencia estudantil", "floram vai a escola", "PDDE", "PDDF",
                                       "maria da penha vai a escola", "escola segura", "mec", "fnde", "secretaria de educacao",
                                       "rede municipal de ensino", "rede municipal de educacao"},
    "Material didático": {"material didatico", "apostilas", "livros didaticos", "paradidaticos", "kits pedagogicos"},
    "Vagas em creches e escolas": {"vagas integrais", "vaga em neim", "vaga em ubm"},
    "Estacionamentos e vagas rotativas": {"vagas de estacionamento", "vagas rotativas", "estacionamento"},
    "Gestão e Regulação da Mobilidade Urbana": {"secretaria municipal de planejamento e inteligencia urbana"},
    "Infraestrutura cicloviária": {"ciclismo", "ciclofaixa", "ciclorrota", "ciclovia", "bicicleta eletrica", "bicicletario", "bicicletas"},
    "Manutenção da infraestrutura viária": {"asfaltamento", "pavimentacao asfaltica", "pavimentacao", "tapa-buracos", "relajotamento"
                                            "reparo na rua", "reparo da rua"},
    "Organização do trânsito": {"cruzamentos", "embarque e desembarque", "carga e descarga", "motofaixas", "nao estacionar",
                                "proibido estacionar", "proibido parar e estacionar", "redutor de velocidade", "redutores de velocidade",
                                "semaforos", "semaforo", "sinaleiras", "sinalizacao", "sinalizacao de transito", "travessia elevada",
                                "faixa elevada", "faixa exclusiva", "faixas", "faixa de pedestre","lombofaixa", "binario", "transito",
                                "mao unica", "guard rail", "guarda corpo", "lombada", "lombo faixa", "fluxo viario", "fluxo de veiculos"},
    "Serviços de transporte individual privado": {"aplicativo de transporte", "uber", "99", "taxi", "transporte por app"},
    "Transporte público": {"cartao de transporte", "vale transporte", "itinerario da linha", "transporte coletivo", "transporte publico", "onibus",
                           "ticen", "tirio", "titri", "tilag", "formiguinha", "passageiros", "linha de transporte", "horarios de onibus"},
    "Direitos e condições de trabalho": {"escala de trabalho", "jornada de trabalho", "abono de faltas"},
    "Promoção do trabalho e da renda": {"programa cuida mais floripa"},
    "Impactos urbanísticos de empreendimentos": {"estudos de impacto", "compensacao ambiental"},
    "Legalização e denominação de vias e espaços públicos": {"denominacao do parque", "denomima praca", "denomimacao da praca",
                                                             "denominacao de via publica", "legaliza via", "legaliza servidao",
                                                             "legalizacao de via publica", "reconhecimento oficial da rua"},
    "Plano diretor": {"plano diretor"},
    "Perímetro urbano e delimitações": {"limite urbano", "institui o bairro"},
    "Regularização fundiária": {"parcelamento do solo", "regularizacao fundiaria", "floripa regular", "programa lar legal", "reurb"},
    "Zoneamento": {"zoneamento"},
    "Poluição sonora": {"caixa de som", "alto-falantes"},
    "Manifestação religiosa": {"manifestacao religiosa"},
    "Decoro e conduta em espaços públicos": {"decoro"},
    "Rede de esgotamento sanitário": {"rede de esgoto", "esgoto", "estacao de tratamento", "esgotamento", "fossa", "fossas", "despejo irregular",
                                      "rede coletora", "manilhas", "encanamento", "sanitario", "sanitaria", "sumidouro", "sumidouros"},
    "Gestão e Regulação dos Serviços de Saneamento": {"concessao de agua"},
    "Rede de drenagem": {"drenagem", "escoamento", "rede pluvial", "galeria pluvial", "bueiro", "bueiros", "boca de lobo", "bocas de lobo"},
    "Rede de abastecimento de água": {"rede de agua", "abastecimento", "encanamento", "tubulacao", "adutora", "cavalete", "hidrometro", "agua potavel",
                                      "fornecimento de agua", "falta de agua", "instalacao hidraulica", "reparo de vazamento"},
    "Controle sanitário e vigilância em saúde": {"proliferacao de dengue", "aedes aegypti", "desratizacao", "irregularidade sanitaria", "proliferacao de pombos", "ratos", "prevencao da dengue"},
    "Equipamentos públicos de saúde": {"cs", "centro de saude", "centros de saude", "posto de saude", "postos de saude", "postinhos de saude", "ubs", "consultorio na rua", "consultorios na rua"},
    "Gestão e Regulação da Saúde Pública": {"programa de vacinacao contra o hpv", "secretaria de estado da saude", "conselho local de saude"},
    "Prevenção e combate de doenças": {"covid-19", "vacina de gripe", "vacina da gripe", "campanha de vacinacao", "vacinacao do hpv", "medicamentos"},
    "Rede de Atenção Psicossocial (RAPS)": {"caps", "capsi"},
    "Gestão e Regulação da Segurança Pública": {"secretaria municipal de seguranca", "conseg", "conselho comunitario de seguranca", "conselho de seguranca"},
    "Infraestrutura de segurança": {"complexo penitenciario","camaras de monitoramento", "camaras de seguranca", "camaras corporais", "delegacia de policia", "reconhecimento facial"},
    "Prevenção e policiamento": {"guarda municipal", "policiamento"},
    "Segurança e monitoramento de espaços públicos": {"controle de acesso"},
    "Violência e criminalidade urbana": {"violencia na rua"},
    "Áreas protegidas e conservação ambiental": {"app", "area de protecao ambiental", "plano municipal de conservacao e recuperacao da mata atlantica",
                                                 "plano de manejo"},
    "Educação ambiental": {"programa lixo zero"},
    "Energia e sustentabilidade": {"sustentabilidade"},
    "Gestão de resíduos": {"reciclagem"},
    "Gestão e proteção de corpos hídricos e áreas associadas": {"desassoreamento", "dragagem", "canal da barra da lagoa"},
    "Governança ambiental": {"fundacao municipal do meio ambiente", "floram", "defesa civil"},
    "Instrumentos de regulação e controle ambiental": {"licenciamento ambiental", "avaliacao de impacto", "outorgas ambientais", "fiscalizacao ambiental"},
    "Mudanças climáticas": {"emergencia climatica", "mudancas climaticas"},
    "Vegetação e arborização urbana": {"arborizacao", "plantio"},
    "Limpeza Urbana": {"comcap", "conteiner", "contentor", "contentor de lixo", "contentores de lixo",
                       "coleta seletiva", "corte de arvore", "corte de mato", "entulho", "hidrojateamento",
                       "hidrojato", "limpeza", "limpeza da rua", "limpeza de vala", "limpeza na rua",
                       "limpeza urbana", "lixeira", "lixeiras", "lixo", "lixo pesado", "poda",
                       "raspagem de sargetas", "reposicao de lixeiras", "residuos", "residuos solidos",
                       "retentor de lixo", "rocada", "rocagem", "seletiva"},
    "Manutenção de rede elétrica": {"transformador"},
    "Iluminação pública": {"iluminacao publica", "poste de luz", "luminaria publica", "iluminacao"},
    "Gestão e Regulação da Zeladoria Urbana": {"secretaria municipal de limpeza e manutencao urbana"},
    "Obras e Reparos Urbanos": {"muro de contencao"},
}


MAP_REGIOES =  {
    "Canasvieiras/SC": ["canasvieiras", "jurere", "jurere internacional", "mangue de jurere", "daniela", "rio da palha", "vargem de fora", "ebm professora iracema brito andrade", "ebm osmar cunha", "ebm virgilio dos reis varzea"],
    "Cachoeira do Bom Jesus/SC": ["vargem grande", "vargem do bom jesus", "cachoeira do bom jesus", "ponta das canas", "praia brava", "lagoinha do norte", "ebm albertina madalena dias", "ebm intendente aricomedes da silva (ebias)", "ebm luiz candido da luz", "ebm osvaldo machado"],
    "Ingleses do Rio Vermelho/SC": ["ingleses", "dunas dos ingleses", "capivari", "santinho", "herondina medeiros zeferino", "ebm maria tomazia coelho", "ebm professora neuza paula da silveira", "comunidade do siri"],
    "Santo Antônio de Lisboa/SC": ["santo antonio de lisboa", "cacupe", "sambaqui", "barra do sambaqui", "praia do paulino", "rio do verissimo", "recanto dos acores", "mangue de ratones", "ebm marcolino jose de lima", "ebm paulo fontes"],
    "Ratones/SC": ["ratones", "vargem pequena", "canto da cachoeira", "canto da moreira", "ebm mancio costa", "ebm professora zulma freitas de souza", "ebm zulma freitas de souza"],
    "São João do Rio Vermelho/SC": ["rio vermelho", "mocambique", "muquem", "parque florestal", "ebm antonio paschoal apostolo", "ebm darcy ribeiro", "ebm maria conceicao nunes"],
    "Saco Grande/SC": ["saco grande", "joao paulo", "monte verde", "ebm donicia maria da costa", "ebm jose do valle pereira", "neim vila cachoeira"],
    "Estreito/SC": ["bairro de fatima", "grota", "jardim atlantico", "balneario", "marinha", "canto", "estreito", "morro da caixa", "capoeiras", "monte cristo", "coloninha", "chico mendes", "sape"],
    "Coqueiros/SC": ["coqueiros", "vila aparecida", "abraao", "bom abrigo", "itaguacu", "ebm almirante carvalhal"],
    "Sede/SC": ["centro", "jose mendes", "mocoto", "monte serrat", "agronomica", "ebm osvaldo galupo", "neim celso ramos"],
    "Saco dos Limões/SC": ["ocupacao marielle franco", "saco dos limoes", "costeira do pirajubae", "carvoeira", "serrinha", "ebm adotiva liberato valentim", "ebm jose jacinto cardoso", "ebb julia da costa neves"],
    "Trindade/SC": ["trindade", "itacorubi", "corrego grande", "santa monica", "parque sao jorge", "pantanal", "ebm beatriz de souza brito", "ebm joao alfredo rohr", "ebm vitor miguel de souza"],
    "Lagoa da Conceição/SC": ["morro da lagoa", "lagoa da conceicao", "costa da lagoa", "ponta da aroeira", "canto dos aracas", "canto da lagoa", "porto da lagoa", "costao da joaquina", "dunas da lagoa", "ebm costa da lagoa", "ebm henrique veras", "ebm joao francisco garcez"],
    "Barra da Lagoa/SC": ["barra da lagoa", "praia mole", "galheta", "retiro", "ebm acacio garibaldi sao thiago", "ebm retiro da lagoa"],
    "Tapera da Base/SC": ["tapera", "carianos", "ressacada", "base aerea", "mangue do aeroporto", "campus ufsc", "morro do peralta", "ebm escola do futuro", "neim jose rodrigues willamil"],
    "Campeche/SC": ["campeche", "rio tavares", "morro das pedras", "pedrita", "morro do lampiao", "moeda", "autodromo", "lavouras", "ebm brigadeiro eduardo gomes", "ebm joao goncalves pinheiro", "ebm jose amaro cordeiro"],
    "Ribeirão da Ilha/SC": ["alto ribeirao", "ribeirao da ilha", "barro vermelho", "freguesia do ribeirao", "costeira do ribeirao", "caiacanga", "tapera do ribeirao", "naufragados", "batista pereira", "lupercio belarmino da silva"],
    "Pântano do Sul/SC": ["pantano do sul", "armacao", "lagoa do peri", "sertao do peri", "restinga do peri", "matadeiro", "ponta do facao", "acores", "rio das pacas", "saco da baleia", "costa de dentro", "ebm costa de dentro", "ebm dilma lucia dos santos", "praia da solidao"]
}

CORRECAO_ORTOGRAFICA = {
    "adequacao": "adequação", "adequacoes": "adequações", "aguas": "águas", "asfalatico": "asfáltico", "audiencia publica": "audiência pública",
    "calcada": "calçada", "calcadas": "calçadas", "capelas mortuarias": "capelas mortuárias", "cartao de passe": "cartão de passe", "castracao": "castração",
    "centro de saude": "centro de saúde", "centros de saude": "centros de saúde", "cidada honoraria": "cidadã honorária", "cidadao honorario": "cidadão honorário",
    "conservacao": "conservação", "corrimao": "corrimão", "denominacao": "denominação", "desobstrucao": "desobstrução", "educacao infantil": "educação infantil",
    "extensao": "extensão", "fiscalizacao": "fiscalização", "frota de onibus": "frota de ônibus", "iluminacao": "iluminação", "iluminacao publica": "iluminação pública",
    "instalacao": "instalação", "linha de onibus": "linha de ônibus", "linhas de onibus": "linhas de ônibus", "luminaria publica": "luminária pública",
    "manutencao": "manutenção", "manutencoes": "manutenções", "mocao de aplausos": "moção de aplausos", "mocao de protesto": "moção de protesto",
    "mocao de repudio": "moção de repúdio", "modernizacao": "modernização", "onibus": "ônibus", "pavimentacao": "pavimentação", "posto de saude": "posto de saúde",
    "postinhos de saude": "postinhos de saúde", "postos de saude": "postos de saúde", "praca": "praça", "recolocacao": "recolocação", "reconstrucao": "reconstrução",
    "recuperacao": "recuperação", "reinstalacao": "reinstalação", "reparacao": "reparação", "residuos": "resíduos", "restauracao": "restauração",
    "revitalizacao": "revitalização", "rocagem": "roçagem", "saude": "saúde", "seguranca": "segurança", "semaforica": "semafórica",
    "servidao": "servidão", "sinalizacao": "sinalização", "substituicao": "substituição", "unidade basica de saude": "unidade básica de saúde",
    "unidades basicas de saude": "unidades básicas de saúde", "utilidade publica": "utilidade pública", "via publica": "via pública"
}
