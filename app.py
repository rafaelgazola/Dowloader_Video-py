import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from flask import Flask, jsonify, render_template, request, send_file
from pytubefix import YouTube
from pytubefix.exceptions import BotDetection, VideoUnavailable
from werkzeug.utils import secure_filename

try:
    from imageio_ffmpeg import get_ffmpeg_exe
except ImportError:
    get_ffmpeg_exe = None


app = Flask(__name__)
app.logger.setLevel(logging.INFO)
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}


def youtube_url(link):
    """Aceita apenas o endereço de um vídeo, nunca um site arbitrário."""
    try:
        url = urlsplit(link.strip())
        if url.scheme not in {"http", "https"} or url.hostname not in YOUTUBE_HOSTS or url.port:
            raise ValueError
        query = parse_qs(url.query, keep_blank_values=True)
        if url.hostname == "youtu.be":
            video_id = url.path.strip("/")
        elif url.path == "/watch":
            video_id = query.get("v", [""])[0]
        else:
            parts = url.path.strip("/").split("/")
            video_id = parts[1] if len(parts) == 2 and parts[0] in {"shorts", "live"} else ""
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            raise ValueError
        return f"https://www.youtube.com/watch?v={video_id}"
    except (AttributeError, ValueError):
        raise ValueError("Cole o link de um único vídeo do YouTube.") from None


def baixar(stream, pasta, nome):
    if stream is None:
        raise ValueError("Não há uma faixa compatível para este vídeo.")
    arquivo = Path(stream.download(output_path=str(pasta), filename=nome)).resolve()
    if arquivo.parent != pasta.resolve():
        raise ValueError("Não foi possível preparar o arquivo.")
    return arquivo


def ffmpeg(mensagem, *args):
    try:
        executavel = get_ffmpeg_exe() if get_ffmpeg_exe else shutil.which("ffmpeg")
        if not executavel:
            raise OSError("FFmpeg nao encontrado")
        subprocess.run(
            [executavel, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)],
            check=True, shell=False, capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        app.logger.error("FFmpeg: %s", exc.stderr.decode(errors="replace")[-1000:])
        raise ValueError(mensagem) from None
    except (OSError, RuntimeError):
        raise ValueError("Não foi possível iniciar o FFmpeg.") from None


def abrir_video(url):
    """Tenta clientes suportados quando o YouTube bloqueia um deles."""
    ultimo_bloqueio = None
    proxy_url = os.getenv("YOUTUBE_PROXY_URL")
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    for client in ("VISION_OS", "WEB", "ANDROID", "IOS", "TV"):
        yt = YouTube(url, client=client, proxies=proxies)
        try:
            streams = yt.streams
            return yt, streams
        except BotDetection as exc:
            app.logger.warning("YouTube bloqueou o cliente %s", client)
            ultimo_bloqueio = exc
    raise ultimo_bloqueio


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.post("/download")
def download():
    link = request.form.get("url", "")
    formato = request.form.get("format", "")
    pasta = None
    enviando = False

    try:
        url = youtube_url(link)
        if formato not in {"mp4", "mp3"}:
            raise ValueError("Escolha vídeo MP4 ou áudio MP3.")

        yt, streams = abrir_video(url)
        if yt.vid_info.get("videoDetails", {}).get("isLiveContent"):
            raise ValueError("Transmissões ao vivo não são suportadas.")
        pasta = Path(tempfile.mkdtemp(prefix="youtube-download-"))

        if formato == "mp4":
            stream = streams.filter(file_extension="mp4").order_by("resolution").desc().first()
            video = baixar(stream, pasta, "video.mp4")
            arquivo = video
            if not stream.is_progressive:
                audio = baixar(streams.get_audio_only(), pasta, "audio.mp4")
                arquivo = pasta / "pronto.mp4"
                ffmpeg("Não foi possível unir vídeo e áudio deste vídeo.",
                       "-i", video, "-i", audio, "-map", "0:v:0", "-map", "1:a:0",
                       "-c", "copy", arquivo)
                video.unlink()
                audio.unlink()
            tipo = "video/mp4"
        else:
            audio = baixar(streams.get_audio_only(), pasta, "audio.mp4")
            arquivo = pasta / "pronto.mp3"
            ffmpeg("Não foi possível converter o áudio deste vídeo.",
                   "-i", audio, "-vn", "-codec:a", "libmp3lame", "-q:a", "2", arquivo)
            audio.unlink()
            tipo = "audio/mpeg"

        nome = (secure_filename(yt.title)[:120].rstrip("._") or "video") + f".{formato}"
        resposta = send_file(arquivo, as_attachment=True, download_name=nome, mimetype=tipo)
        resposta.direct_passthrough = False
        resposta.call_on_close(lambda: shutil.rmtree(pasta, ignore_errors=True))
        resposta.set_cookie("download_ready", "1", max_age=60, samesite="Lax")
        enviando = True
        return resposta
    except BotDetection:
        erro = "O YouTube bloqueou o acesso deste servidor. Tente rodar o app localmente ou configurar outra conexão de saída."
    except VideoUnavailable:
        app.logger.warning("YouTube reported an unavailable video", exc_info=True)
        erro = "Este vídeo está privado ou indisponível."
    except ValueError as exc:
        erro = str(exc)
    except Exception:
        app.logger.exception("Falha no download")
        erro = "Não foi possível baixar este vídeo. Confira o link e tente novamente."
    finally:
        if pasta and not enviando:
            shutil.rmtree(pasta, ignore_errors=True)

    return render_template("index.html", error=erro, url=link, selected_format=formato), 400


if __name__ == "__main__":
    app.run(debug=False)
