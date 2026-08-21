# Sprint E — UX/UI e acessibilidade

## Resultado

A Sprint E reforça a navegação por teclado, o uso mobile e a apresentação inicial sem alterar os fluxos pedagógicos existentes.

## Entregas

- link global “Pular para o conteúdo principal” e destino de foco explícito;
- indicador de foco consistente com alto contraste;
- suporte a `prefers-reduced-motion` e `forced-colors`;
- espaçamento mobile mais seguro no conteúdo principal;
- onboarding responsivo em três etapas, dispensável e persistido localmente;
- menu mobile com semântica de diálogo, `aria-expanded`, foco preso, fechamento por `Esc` e restauração de foco;
- itens ativos das navegações identificados com `aria-current=page`;
- botões de tema, conta e modo Zen com nomes e estados acessíveis;
- busca rápida com semântica de diálogo, nome acessível, status dinâmico e ciclo de foco;
- modal de conta identificado corretamente e erros anunciados como alertas.

## Validação

- TypeScript: aprovado (`tsc --noEmit`);
- ESLint dos arquivos alterados: aprovado;
- inspeção renderizada desktop e mobile em viewport de 390 × 844;
- onboarding percorrido integralmente;
- menu mobile reconhecido como diálogo e navegação principal;
- `Shift+Tab` no primeiro controle retorna ao último, e `Tab` no último retorna ao primeiro;
- `Esc` fecha o menu e devolve o foco ao botão que o abriu;
- `Ctrl+K` abre “Busca rápida” com o campo de busca focado;
- viewport temporário restaurado e servidor local encerrado após o teste.

## Limitação do ambiente

Os componentes de navegação e acessibilidade foram renderizados e testados. Os dados do dashboard permaneceram no fallback porque `FLASK_API_PROXY_SECRET` não está configurado neste ambiente local. Nenhum segredo foi criado ou copiado para contornar essa restrição.
