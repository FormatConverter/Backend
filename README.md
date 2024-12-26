# Audio_Converter_Backend

## Dockerhub Repo

https://hub.docker.com/repository/docker/cliu232/format-converter-docker/general

## Clone the repo

```bash
git clone https://github.com/FormatConverter/Audio_Converter_Backend.git
cd Audio_Converter_Backend
```

## Build docker image (locally)

```bash
sudo docker build -t audio-converter .
```

## run the server (locally)

```bash
sudo docker run -p 5050:5050 audio-converter
```

## Pull image from Dockerhub

```bash
docker pull cliu232/format-converter-docker:$(tagname)
```
