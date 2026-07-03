# ADR-001 — PrestesOS como plataforma modular

## Status

Aprovado.

## Decisão

O PrestesOS deixa de ser um conjunto de scripts e passa a ser uma plataforma modular em Python.

## Motivo

Evitar crescimento desorganizado, facilitar manutenção, permitir plugins, banco de dados, logs, IA e busca semântica.

## Consequências

- Bash será usado apenas como lançador.
- O núcleo será em Python.
- Funcionalidades novas entrarão como módulos/plugins.
- O projeto seguirá estrutura profissional.
