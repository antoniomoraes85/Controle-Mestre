# CONTROLE MESTRE v0.6.1 — Como usar suas pastas existentes

## Dados reconhecidos

Ao lado da pasta `CONTROLE_MESTRE`, você tem `MATERIAL TEÓRICO` e `ANKI`. **Não mova nem renomeie esses diretórios.** O software identifica automaticamente `MATERIAL TEÓRICO` se a aplicação estiver dentro da mesma pasta-mãe (como nas capturas). Se instalar em outro lugar, use **Materiais e Qconcursos → Configurar pasta externa** e cole o caminho completo da pasta `MATERIAL TEÓRICO` do Windows. Depois clique em **Atualizar biblioteca**.

A estrutura aceita nomes numerados e até quatro tipos de pasta por disciplina:

```text
Controle-Mestre-main/
  CONTROLE_MESTRE/                  <-- aplicação atualizada
  MATERIAL TEÓRICO/                 <-- seus próprios PDFs, intactos
    1 - Contabilidade Geral e Avançada SEFAZ RS/
      Teoria Principal/
      Simplificado/
      PASSO ESTRATÉGICO/
      QUESTÕES/
    2 - Contabilidade de Custos/
      Teoria Principal/
      PASSO ESTRATÉGICO/
      QUESTÕES/
    ...
  ANKI/                             <-- seus CSV, VBA e planilhas, intactos
```

## Atualização segura, sem apagar históricos

1. Encerre o Anki e os servidores CONTROLE MESTRE.
2. Faça uma **cópia de segurança** da pasta atual `CONTROLE_MESTRE` ou, no mínimo, de `dados/controle_mestre.db`. Não substitua arquivos sobre uma instalação aberta.
3. Extraia o pacote 0.6.1 em diretório novo. Para identificar a pasta `MATERIAL TEÓRICO` automaticamente, coloque a nova pasta `CONTROLE_MESTRE` na mesma pasta-mãe de `MATERIAL TEÓRICO`; alternativamente configure o caminho na interface.
4. Copie o **banco anterior** `dados/controle_mestre.db` para a nova instalação. Se estiver migrando de uma versão 0.6.1 futura, preserve também o arquivo privado `dados/catalogo/aulas_primeiro_ciclo.csv`. A distribuição atual já inclui esse catálogo.
5. Execute `iniciar_windows.bat`; abra o endereço exibido na janela, normalmente `http://127.0.0.1:8771`.
6. Em **Materiais e Qconcursos**, confira o caminho externo, clique **Atualizar biblioteca** e abra os detalhes das disciplinas para verificar aulas e PDFs identificados.
7. Em **Trilha Fiscal RS + SC**, confira a prévia e a carga horária por dia; só confirme quando estiver de acordo. O plano não é aplicado automaticamente.
8. Abra o Anki Desktop e confira sua coleção com **Revisões e Anki → Verificar conexão**. A integração continua **somente leitura** e não importa automaticamente macros, CSVs nem altera FSRS.

## Catálogo informado pelo titular

| Disciplina | Aulas cadastradas |
|---|---:|
| Contabilidade Geral e Avançada (arquivo tratado como Contabilidade Geral) | 33 |
| Contabilidade de Custos | 8 |
| Análise das Demonstrações Contábeis | 5 |
| Direito Tributário | 23 |
| Reforma Tributária — EC 132/2023 e LC 214/2025 | 15 |
| Reforma Tributária — LC 227/2026 | 8 |
| Direito Constitucional | 18 |
| Direito Administrativo | 15 |
| **Total** | **125** |
| Direito Civil | **Aguardando lista de aulas** |

Os títulos são metadados fornecidos pelo titular, **não um edital oficial e não evidência de estudo realizado**. O catálogo está no arquivo privado `dados/catalogo/aulas_primeiro_ciclo.csv`; não entra no GitHub público.

## Vínculo e limitações atuais

- O arquivo PDF deve conter indicação reconhecível da aula no nome (`aula_00.pdf`, `curso-aula-05.pdf`, `aula_01_parte_II.pdf`, `aula_demo.pdf`). Quando não for possível detectar, preencha o campo da aula em **Vincular**.
- PDF não é lido semanticamente nesta versão. O texto não é enviado à IA, nem armazenado no banco. Nenhum arquivo é copiado ou renomeado.
- PDF de aula diferente **não é sugerido** como se pertencesse à atividade atual.
- A trilha usa aulas fornecidas para novas semanas. Assuntos genéricos históricos e tarefas anteriores continuam no SQLite para evitar perda de registros. Não há migração retroativa do progresso.
- O planejamento propõe teoria → questões → Passo → revisão por questões; o caderno de erros depende de erros efetivamente registrados. A quantidade de minutos é estimativa, não regra cientificamente validada.
- A pasta externa deve existir e ter o nome `MATERIAL TEÓRICO` (ou sem acento). O servidor local aceita o caminho apenas após confirmação explícita e funciona em loopback.
- O acervo é particular. **Não faça upload de PDFs, banco de dados, planilha com histórico pessoal ou catálogo privado para o GitHub público.**
- O arquivo de macros `SEFAZ_RS_Painel.xlsm`, módulos VBA e os CSVs no diretório `ANKI` não foram editados; devem ser tratados separadamente após auditoria das integrações.

## Verificação

`python -m unittest discover -s tests -q`

A interface precisa ser testada na sua instalação Windows; os testes de backend utilizam apenas arquivos sintéticos.