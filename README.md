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

## Como usar

### 1. Fork/clone este repo no GitHub

### 2. Configurar o repositório como público ou habilitar GHCR

### 3. Push na main dispara o build-sign automaticamente

### 4. Executar verify manualmente via workflow_dispatch

### 5. Gerar relatório de auditoria
```bash
python audit/audit_rekor.py --image ghcr.io/SEU_USUARIO/SEU_REPO --json
```
