# SECURITY.md — Segurança, Privacidade e Dados

## Princípios

- Dados do usuário pertencem ao usuário.
- Nunca apagar arquivos sem confirmação.
- Nunca enviar dados sensíveis para IA externa sem autorização.
- Preferir processamento local quando possível.
- Credenciais nunca devem ser versionadas.

## Proibido

- Salvar API keys no código.
- Expor transcrições privadas em logs.
- Fazer sync automático sem configuração explícita.
- Remover backups.

## Recomendações

- Usar `.env` para segredos.
- Usar `.gitignore` para database, logs e dados pessoais.
- Criar backup antes de migrações.
