This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Desenvolvimento local

O frontend encaminha as chamadas `/api/*` para o Flask em `http://127.0.0.1:5050`.
Por isso os dois processos precisam estar ativos durante o desenvolvimento.

1. Confirme que `app/frontend/.env.local` e `app/backend/.env` têm o mesmo
   `FLASK_API_PROXY_SECRET` e que `FLASK_API_URL=http://127.0.0.1:5050` no
   frontend. Não use uma variável `NEXT_PUBLIC_*` para esse segredo.
2. Em um terminal, inicie o backend:

```powershell
cd app/backend
.\.venv\Scripts\python.exe app.py
```

3. Em outro terminal, inicie o frontend:

```bash
cd app/frontend
npm run dev
```

Abra [http://localhost:3000](http://localhost:3000). Se o dashboard não
carregar, valide a conexão pelo navegador em
`http://localhost:3000/api/stats/overview`; a resposta deve ser JSON com HTTP
200, não uma página de erro do Next.

O servidor Flask pode ser encerrado com `Ctrl+C`. As variáveis de ambiente do
frontend devem ficar em `.env.local`; o Next só as lê na raiz de
`app/frontend`.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
