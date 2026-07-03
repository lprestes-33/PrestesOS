# QA.md — Qualidade e Testes

## Política de qualidade

Nenhuma funcionalidade é considerada pronta sem:

- teste básico;
- documentação mínima;
- registro no CHANGELOG;
- tratamento de exceções;
- validação no Termux quando aplicável.

## Tipos de teste

- Unitário: services isolados.
- Integração: fluxo entre services.
- Regressão: bugs já corrigidos.
- Smoke test: comando `prestes`.

## Critérios mínimos

Antes de concluir tarefa:

```bash
pytest
prestes
```

Se pytest não estiver instalado, registrar isso e sugerir instalação.
