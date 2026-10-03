# YouTube Downloader

Uma página simples para colar o link de **um vídeo público do YouTube** e receber MP4 ou MP3 no navegador. Não há limite de duração ou tamanho definido no aplicativo.

No MP4, o app escolhe a faixa de maior resolução disponível. Se ela vier sem som, baixa o áudio separadamente e une as faixas com FFmpeg, **sem recodificar o vídeo**. No MP3, converte a faixa de áudio. O executável do FFmpeg vem junto com `imageio-ffmpeg`; você não precisa instalá-lo separadamente. Os arquivos ficam em uma pasta temporária e são removidos após o envio.

## Rodar no VS Code (Windows)

Instale [Python](https://www.python.org/downloads/). Abra esta pasta no VS Code e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Se a ativação for bloqueada, rode `Set-ExecutionPolicy -Scope Process Bypass` no mesmo terminal. Acesse **http://127.0.0.1:5000**. Teste as duas opções com o link de um vídeo público. A rota **http://127.0.0.1:5000/health** retorna `{"status":"ok"}`.

## Publicar no Render

Crie um repositório vazio no GitHub e envie estes arquivos:

```powershell
git init
git add .
git commit -m "YouTube Downloader"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

No [Render](https://dashboard.render.com/), escolha **New > Blueprint**, conecte o repositório e confirme. O `render.yaml` usa o `Dockerfile`, que já instala Python, FFmpeg e as dependências. O serviço abre na URL fornecida pelo Render. A verificação de disponibilidade usa a conexão TCP padrão do Render, para que um download longo não bloqueie uma checagem HTTP em `/health`.

## Arquivos

- `app.py`: três rotas e o download;
- `templates/index.html` e `static/style.css`: página;
- `requirements.txt`: dependências Python;
- `Dockerfile` e `render.yaml`: publicação;
- `.gitignore`: evita enviar ambiente virtual e downloads ao GitHub.

## Limites práticos

O aplicativo processa um vídeo por vez. Playlists, lives, vídeos privados e vídeos que exigem autenticação não são suportados. A duração do vídeo não é limitada pelo código. Para MP4 em alta resolução, o disco temporário precisa guardar vídeo, áudio e o arquivo unido durante o processamento; o pico pode se aproximar do dobro do tamanho final.

Para sets longos, há três caminhos simples:

- **Render gratuito:** experimente primeiro. Funciona se o arquivo couber no espaço temporário e o processamento mais envio terminar dentro do [limite de até 100 minutos por resposta HTTP](https://render.com/docs/render-vs-vercel-comparison). O [serviço gratuito pode reiniciar e seus arquivos temporários não persistem](https://render.com/docs/free).
- **Render pago:** mais recursos de CPU/memória e, se necessário, disco persistente. O limite da resposta HTTP ainda se aplica.
- **Local ou VPS com disco suficiente:** melhor opção para sets realmente enormes ou downloads que podem passar do limite de tempo do Render. O mesmo projeto roda sem mudanças na lógica.

Baixe apenas conteúdo que você tem permissão para usar.
