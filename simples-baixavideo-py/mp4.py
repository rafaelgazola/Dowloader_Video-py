from pytubefix import YouTube

url = str(input("DIGITE O LINK DO VIDEO: "))

yt = YouTube(url)

print(f"Baixando: {yt.title}")

stream = yt.streams.filter(
    file_extension="mp4"
).order_by("resolution").desc().first()

if stream:
    stream.download()
    print("Download concluído com sucesso!")
else:
    print("Não foi possível encontrar um formato compatível.")