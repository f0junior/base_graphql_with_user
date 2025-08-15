# Comandos para rodar após baixar o projeto

1. Rodar o comando global
```
poetry config virtualenvs.in-project true
```
2. Remover o ambiente atual (opcional mas recomendado):
```
cd backend
poetry env remove python
```
3. Criar a nova venv dentro do projeto:
```
poetry install
```
Isso vai criar um .venv/ na pasta backend/, bonitinho.

✅ Depois disso no VSCode
Configure o settings.json com caminho relativo:

### Windows:
```
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe"
}
```
### Linux/macOS:
```
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
}
```

Ou Pressione `Ctrl + Shift + P`, digite `Python: Select Interpreter`, clique em
`Enter interpreter path` e coloque o caminho para a pasta conforme indicado acima para os casos **windows** ou **linux/macOS** criada dentro de **backend**

E pronto! Portável, limpo, e o Pylance vai parar de fingir que não conhece seus pacotes. 😎