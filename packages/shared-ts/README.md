# shared-ts

Espaco reservado para contratos e utilitarios TypeScript compartilhados entre backend e dashboard.

## Regras

- centralizar tipos operacionais reaproveitaveis
- manter fronteiras claras entre apresentacao e dominio
- evitar dependencias pesadas durante o bootstrap

## Artefatos atuais

- `src/telemetry.ts` mantem os tipos do read model atual.
- `src/control-plane/` passa a expor os contratos de dominio, actions e capabilities do Mark 1.

## Papel no Mark 1

- compartilhar o modelo de control plane entre UI, servicos e futuras integrações programaticas
- evitar que a UI modele actions/capabilities por conta propria
- preservar a compatibilidade Mark 1 -> Mark 2 com metadata extensivel de capability
- espelhar DTOs nominais e regras de availability do pacote Python
- validar a superfície compartilhada com teste contratual em `tests/control-plane.test.ts`
