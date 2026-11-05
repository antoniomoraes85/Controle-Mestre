# Dados e privacidade

O CONTROLE MESTRE v0.1 é um programa local, monousuário e sem autenticação.

## O que pode ir para o GitHub

- Código-fonte, testes e documentação genérica.
- Modelos vazios, exemplos sintéticos explicitamente identificados.
- Regras de planejamento explicadas e versões de interface.

## O que NÃO pode ir para o GitHub público

- Bancos SQLite ou backups contendo histórico pessoal.
- Planilhas reais, exportações do Anki, logs individuais e dados de candidatos.
- Informações de saúde, dados financeiros, senhas, tokens, chaves e segredos.
- Apostilas, PDFs e bancos de questões de terceiros sem licença de redistribuição.

## Regras de desenvolvimento

1. Manter o banco pessoal fora do controle de versão, em `dados/controle_mestre.db`.
2. Usar variáveis de ambiente para localização de dados e credenciais.
3. Provar importação idempotente e evitar dupla contabilização de horas Anki/Excel.
4. Para lançamento SaaS: autenticação, isolamento por usuário, criptografia, logs seguros, backup restaurável, controle de acesso, políticas de privacidade e processo de exclusão de dados.
5. Não publicar a versão local atual em um servidor acessível ao público.

**Atenção:** criar uma assinatura comercial exige infraestrutura e políticas de segurança adicionais.
