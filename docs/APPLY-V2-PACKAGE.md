# Apply V2 Package

## Objetivo
Aplicar rapidamente o pacote no repositório atual.

## Passos
1. criar branch: `refactor/v2-control-plane`
2. copiar o conteúdo deste pacote para a raiz do repositório
3. revisar:
   - `AGENTS.md`
   - `.agents/`
   - `.codex/skills/`
   - `docs/v2/`
4. commitar só a camada de documentação/governança
5. abrir o Codex
6. usar `docs/v2/INITIAL-CODEX-REFACTOR-PROMPT.md`
7. pedir geração da board expandida
8. revisar a board
9. iniciar implementação pela primeira fase

## Não fazer
- não misturar este commit com implementação
- não deixar agentes antigos convivendo com os novos
- não começar pela UI antes de a board existir
