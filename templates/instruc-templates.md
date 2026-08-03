# instruçoes de templates

- WebApp mobile first pensado para o uso rápido e simples para leitura de infromações
- Também acesso via computador então responsividade é importante
- O template deve ser responsivo
- O template deve ser leve e rápido
- botões devem respeitar as cores definidas para o template.

## cores definidas no template

- primary: #3C89E5 
- secondary: #EC3D6E
- tertiary: #04AABB
- quaternary: #F7B538
- quinary: #FFFFFF

## fontes definidas da marca

- oswald
- sans-serif

## framework para templates

- tailwind forms (https://pypi.org/project/crispy-tailwind/)
- bulma.io (https://bulma.io/documentation/start/responsiveness/)


## login
📁 Estrutura básica de templates do django-allauth

O projeto inclui várias pastas de templates principais:

account/ — autenticação local (login, signup, senha etc)

socialaccount/ — login via providers sociais (Google, GitHub etc)

mfa/ — multi-fator (se usado)

allauth/ — layouts e elementos base para todos os templates

Você deve criar pastas com os mesmos nomes dentro de templates/ no seu projeto para que o Django encontre e use suas versões personalizadas.

✅ Templates comuns que você vai querer sobrescrever
🧑‍💻 Templates de entrada / login / registro

Estes ficam dentro de templates/account/:

login.html – página de login padrão (entrada de email/senha)

signup.html – página de cadastro ou registro de conta

logout.html – confirmação de logout (pode ser útil)

password_change.html – alterar senha (página “alterar senha”)

password_set.html – configurar nova senha sem antiga

password_reset.html – página que envia email de reset

password_reset_done.html

password_reset_from_key.html – pagina onde usuário digita nova senha com token

password_reset_from_key_done.html

email_confirm.html – confirmação de email após clique no link

email_confirm_done.html

(Essa lista é representativa; o Allauth pode ter mais se recursos extras estiverem habilitados, mas os principais acima são os padrões que você vai personalizar primeiro.)

📱 Templates de Social Login

Na pasta templates/socialaccount/ (relevante se você está usando sign-in com redes sociais):

signup.html – página mostrada quando social login precisa completar registro

login.html – (nem sempre existe por padrão: social login é integrado dentro do account/login.html via includes)

snippets/provider_list.html – lista de botões de provedores (Google, GitHub, etc)

snippets/login_extra.html – partes extras da interface social

Esses são incluídos dentro do template de login principal para montar os botões de social login.

📌 Como sobrescrever (resumo prático)

Crie a pasta de templates no seu projeto:

templates/
  account/
    login.html
    signup.html
    ...
  socialaccount/
    signup.html
    snippets/provider_list.html
    ...
  allauth/
    layouts/base.html
    layouts/entrance.html
    layouts/manage.html
    ...