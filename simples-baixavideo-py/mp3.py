import os
from pytubefix import YouTube

# Solicita o link do vídeo
url = str(input("DIGITE O LINK DO VIDEO: "))

yt = YouTube(url)

print(f"Baixando: {yt.title}")

# Seleciona apenas a trilha de áudio
stream = yt.streams.get_audio_only()

if stream:
    # Faz o download do arquivo de áudio padrão (geralmente .m4a ou .webm)
    arquivo_original = stream.download()
    
    # Separa o nome do arquivo da extensão antiga
    nome_base, _ = os.path.splitext(arquivo_original)
    
    # Define o novo nome com a extensão .mp3
    novo_arquivo = nome_base + ".mp3"
    
    # Renomeia o arquivo no seu computador
    os.rename(arquivo_original, novo_arquivo)
    
    print("Download concluído com sucesso em formato MP3!")
else:
    print("Não foi possível encontrar um formato de áudio compatível.")
