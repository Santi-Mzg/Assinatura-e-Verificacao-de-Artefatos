# Secure Artifact Signing – Demo

Projeto para demonstração de assinatura e verificação de artefatos Docker
com Cosign e Sigstore. Trabalho de Segurança de Software – UFSC 2025.

## Estrutura

```
.
├── app/
│   ├── app.py           # API Flask (2 endpoints)
│   └── requirements.txt
├── Dockerfile
├── audit/
│   └── audit_rekor.py   # Consulta log Rekor e gera relatório HTML
└── .github/
    └── workflows/
        ├── build-sign.yml  # Build + push + assinatura keyless
        └── verify.yml      # Verificação + deploy (3 cenários)
```
