# Base GraphQL com Usuário

Este repositório serve como base para criação de APIs GraphQL utilizando as seguintes tecnologias:

- **FastAPI**: Framework web assíncrono e rápido para Python.
- **Strawberry**: Biblioteca para GraphQL em Python, fácil de usar e tipada.
- **Pydantic**: Validação e serialização de dados baseada em tipos.
- **SQLAlchemy**: ORM para manipulação de banco de dados relacional.
- **Redis**: Armazenamento em memória para controle de sessões.

## Funcionalidades

- Estrutura pronta para API GraphQL.
- Endpoint para autenticação e acesso de usuário.
- Controle de sessão de usuário salvo em Redis.
- Exemplos de mutações e queries para cadastro, login, consulta e atualização de usuário.

## Como usar

1. Instale as dependências com [Poetry](https://python-poetry.org/).
2. Inicie os serviços necessários (Redis, banco de dados).
3. Execute a aplicação com o script `start.sh`.

Consulte os exemplos de requisições em [example.http](example.http)