# CONTROLE MESTRE v0.4 — instruções de uso

## Atualizar sem perder o banco pessoal
1. Feche a versão antiga.
2. Copie **seu** arquivo `dados/controle_mestre.db` para uma pasta segura.
3. Extraia o arquivo ZIP da v0.4 em uma nova pasta.
4. Copie o banco antigo para a subpasta `dados` da instalação nova.
5. Execute `iniciar_windows.bat` e abra http://127.0.0.1:8765.
6. No menu, abra **Simulados e redações** para lançar avaliações.

A versão web local requer Python 3.11 ou superior. Não exige Node.js. O código do Streamlit foi preservado como opção legada.

## Entregas da v0.4
- Módulos ES nativos para formatos, requisições HTTP e avaliações.
- Simulados: acertos, erros, brancos, chutes e notas opcionais.
- Redações: tema, banca, nota e nota máxima.
- Migração SQLite aditiva. Questões avulsas e simulados não são somados.
- Testes automatizados Python e CI do GitHub.

## Limites conhecidos
Não há login, hospedagem pública, assinatura, sincronização automática com Anki ou acesso multiusuário. O serviço deve continuar restrito a 127.0.0.1.

## Qualidade e próximos passos
Foram executados 25 testes Python e teste de renderização de componentes pelo Node. O navegador automatizado neste ambiente bloqueou acesso a páginas por configuração administrativa: é necessária conferência visual no Windows.

A implementação futura de contas, banco PostgreSQL e separação de dados está documentada em [ADR-002](docs/ADR-002-CAMINHO-PARA-SAAS.md).