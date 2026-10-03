# YouTube Downloader

Uma página simples para colar o link de **um vídeo público do YouTube** e receber MP4 ou MP3 no navegador. Não há limite de duração ou tamanho definido no aplicativo.

No MP4, o app escolhe a faixa de maior resolução disponível. Se ela vier sem som, baixa o áudio separadamente e une as faixas com FFmpeg, **sem recodificar o vídeo**. No MP3, converte a faixa de áudio. No Windows e no Render, o executável do FFmpeg vem junto com `imageio-ffmpeg`; no Android, usa o pacote `ffmpeg` do Termux. Os arquivos ficam em uma pasta temporária e são removidos após o envio.

## Rodar no VS Code (Windows)

Instale [Python](https://www.python.org/downloads/). Abra esta pasta no VS Code e execute:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Se a ativação for bloqueada, rode `Set-ExecutionPolicy -Scope Process Bypass` no mesmo terminal. Acesse **http://127.0.0.1:5000**. Teste as duas opções com o link de um vídeo público. A rota **http://127.0.0.1:5000/health** retorna `{"status":"ok"}`.

## Rodar no Android quando precisar

Esta opção é gratuita e não precisa deixar um computador ligado em casa. O download usa a conexão do celular, então o Termux precisa ficar rodando até terminar. Instale o [Termux pelo F-Droid](https://f-droid.org/en/packages/com.termux/) ou pela [página oficial do projeto](https://github.com/termux/termux-app); a versão da Play Store pode ter limitações.

No Termux, execute uma vez:

```sh
pkg update && pkg upgrade
pkg install python ffmpeg git
git clone https://github.com/rafaelgazola/Dowloader_Video-py.git
cd Dowloader_Video-py
python -m pip install -r requirements-android.txt
```

Para usar depois, abra o Termux e execute:

```sh
cd Dowloader_Video-py
python app.py
```

Abra **http://127.0.0.1:5000** no navegador do celular. Para encerrar, volte ao Termux e pressione **Ctrl+C**. Se o Android encerrar o Termux durante um download, desative a otimização de bateria para o aplicativo.

### Abrir em outro PC enquanto o celular está rodando

Abra uma **segunda sessão** no Termux e execute:

```sh
pkg install cloudflared
cloudflared tunnel --url http://localhost:5000 --allowed-mail seu-email@exemplo.com
```

Troque o endereço pelo seu email. Abra no PC o link `https://...trycloudflare.com` exibido pelo comando e confirme o código enviado ao email. O link é temporário, muda a cada execução e só funciona enquanto `python app.py` e `cloudflared` estiverem rodando no celular. O acesso por email protege a página, que permite iniciar downloads. [Cloudflare Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/) são voltados a testes e não garantem disponibilidade permanente.

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

No [Render](https://dashboard.render.com/), escolha **New > Blueprint**, conecte o repositório e confirme. O `render.yaml` usa o `Dockerfile`, que instala Python e as dependências; o FFmpeg vem no pacote `imageio-ffmpeg`. O serviço atual, [youtube-downloader](https://youtube-downloader-0d90.onrender.com), foi criado diretamente no Render com runtime Python, `pip install -r requirements.txt` e `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 0`. A verificação de disponibilidade usa a conexão TCP padrão do Render, para que um download longo não bloqueie uma checagem HTTP em `/health`.

O YouTube pode identificar o IP de saída do Render como bot. Nesse caso, `/health` continua respondendo, mas o download falha. Para usar outra conexão de saída, configure `YOUTUBE_PROXY_URL` nas variáveis de ambiente do serviço Render com a URL de um proxy HTTP(S) confiável (por exemplo, `http://usuario:senha@host:porta`). Guarde essa URL apenas no Render, nunca no repositório. O funcionamento depende de o YouTube aceitar o IP do proxy. Sem um proxy aceito, rode o app localmente ou em uma rede cujo IP seja aceito pelo YouTube.

## Arquivos

- `app.py`: três rotas e o download;
- `templates/index.html` e `static/style.css`: página;
- `requirements.txt`: dependências Python;
- `Dockerfile` e `render.yaml`: publicação;
- `.gitignore`: evita enviar ambiente virtual e downloads ao GitHub.

## Limites práticos

O aplicativo processa um vídeo por vez. Playlists, lives, vídeos privados e vídeos que exigem autenticação não são suportados. A duração do vídeo não é limitada pelo código. Para MP4 em alta resolução, o disco temporário precisa guardar vídeo, áudio e o arquivo unido durante o processamento; o pico pode se aproximar do dobro do tamanho final.

Para sets longos, há três caminhos simples:

- **Render gratuito:** depende de o YouTube aceitar o IP de saída, além de o arquivo caber no espaço temporário e o processamento mais envio terminar dentro do [limite de até 100 minutos por resposta HTTP](https://render.com/docs/render-vs-vercel-comparison). O [serviço gratuito pode reiniciar e seus arquivos temporários não persistem](https://render.com/docs/free).
- **Render pago:** mais recursos de CPU/memória e, se necessário, disco persistente. O limite da resposta HTTP ainda se aplica.
- **Local ou VPS com disco suficiente:** melhor opção para sets realmente enormes ou downloads que podem passar do limite de tempo do Render. O mesmo projeto roda sem mudanças na lógica.

Baixe apenas conteúdo que você tem permissão para usar.
