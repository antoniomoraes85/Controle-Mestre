# CONTROLE MESTRE v0.6.2 — Correção do catálogo e integração TEC Avançado

## Diferença essencial: 125 aulas não significam 125 PDFs

- **125 aulas cadastradas:** estão em `dados/catalogo/aulas_primeiro_ciclo.csv` com títulos e assuntos fornecidos pelo usuário. O menu **Materiais e TEC Concursos** agora mostra esse catálogo, mesmo quando não há PDFs acessíveis.
- **PDFs catalogados:** são os arquivos `.pdf` existentes no computador e que a aplicação consegue localizar. Sem localizar a pasta, o número permanece em zero. Nenhum PDF foi enviado com o ZIP e nenhum PDF foi enviado ao GitHub.
- **Direito Civil:** permanece nas nove disciplinas, aguardando lista de aulas; não há aulas inventadas.

## Onde seus materiais devem continuar

```text
Controle-Mestre-main/
  CONTROLE_MESTRE/       ← nova instalação, arquivo iniciar_windows.bat
  MATERIAL TEÓRICO/      ← seus PDFs, NÃO MOVER
    1 - Contabilidade Geral e Avançada SEFAZ RS/
      Teoria Principal/
      Simplificado/
      PASSO ESTRATÉGICO/
      QUESTÕES/
    ...
  ANKI/                  ← seu histórico, CSV e XLSM, NÃO ALTERAR
```

No Windows, a pasta `MATERIAL TEÓRICO` pode estar em outro local. A aplicação mostra o **caminho esperado** na tela, mas pode configurar o caminho verdadeiro manualmente.

### Como localizar os PDFs sem copiar arquivos

1. Abra o Explorador de Arquivos diretamente na pasta `MATERIAL TEÓRICO` (não dentro de uma disciplina).
2. Clique na barra de endereços do Explorador (atalho `Alt+D`) e copie o caminho completo (`Ctrl+C`).
3. No CONTROLE MESTRE, abra **Materiais e TEC Concursos → Configurar pasta externa**.
4. Cole o caminho completo e confirme a leitura local.
5. Clique em **Atualizar biblioteca** e verifique a contagem de PDFs. A biblioteca reconhecerá `Aula 00`, `Aula 01`, `Aula 01 - Parte II` etc. quando constarem no nome do PDF; nomes ambíguos exigem vínculo manual.
6. Expanda **Catálogo de aulas fornecido por você** e confira quantas aulas estão associadas a documentos. PDF encontrado não equivale a aula concluída.

Se aparecer `0 PDFs`, verifique que as subpastas contêm arquivos `.pdf` (e não apenas subpastas vazias). Capturas mostrando diretórios não comprovam que os PDFs já estejam dentro deles.

## TEC Concursos Avançado: integração inicial permitida

- O painel passa a ter **Meus cadernos TEC Concursos**, botão **Salvar link** e abertura pelo site autenticado do TEC.
- Para salvar um caderno, entre no TEC, abra o caderno desejado e copie o endereço da barra do navegador. O endereço deve ser HTTPS em `tecconcursos.com.br` ou `www.tecconcursos.com.br`.
- Para estatísticas, cadastre as questões manualmente em **Questões** com plataforma `TEC Concursos`; ou prepare um CSV com suas próprias contagens (não é garantida exportação nativa do site).
- Formato: `data;disciplina;assunto;total;acertos;banca;link;id`. Use `id` único para cada bateria. Salve o CSV em `CONTROLE_MESTRE/dados/importacoes/tec/`. Abra **Materiais e TEC Concursos → Pré-visualizar resultados** e só então confirme.
- O banco antigo mantém os registros que eventualmente tenham vindo do Qconcursos, mas o painel principal agora usa TEC. NUNCA importe a mesma bateria do TEC também como registro manual: as versões atuais não têm conciliação automática entre fontes diferentes.
- **Não há acesso direto à conta do TEC, scraping, API não documentada, importação de enunciados ou sincronização automática** na v0.6.2.

## Atualização segura da v0.6.1

1. Feche a janela/servidor antigo antes de testar a nova versão, especialmente se estava na porta 8771.
2. Faça cópia da pasta `CONTROLE_MESTRE` atual; não exclua sua pasta `MATERIAL TEÓRICO` nem `ANKI`.
3. Descompacte o ZIP v0.6.2 em **nova pasta** e execute a partir do `iniciar_windows.bat` dessa pasta.
4. Se houver histórico real, copie o `dados/controle_mestre.db` anterior **com a aplicação fechada**. Preserve a cópia original. O catálogo `dados/catalogo/aulas_primeiro_ciclo.csv` já está no ZIP; se você o editou manualmente, preserve sua versão.
5. Abra `/api/health` no endereço mostrado pelo terminal e confira versão **0.6.2**. Normalmente `http://127.0.0.1:8771/api/health`.
6. Se a página ainda mostrar `Qconcursos`, feche servidores anteriores, atualize com `Ctrl+Shift+R` e confirme que o navegador está na porta da nova instância.

## O que foi verificado

- Testes Python em SQLite temporário, sem acesso ao banco pessoal.
- Teste de HTML do catálogo no Node.js mostra 125 aulas mesmo sem PDFs; rotas TEC e deduplicação de CSV exercitadas.
- A instalação no seu Windows e a conexão com seu acervo/Anki reais **continuam pendentes de homologação**.
- A versão não altera o Anki FSRS, a planilha XLSM ou seus arquivos `.bas`.