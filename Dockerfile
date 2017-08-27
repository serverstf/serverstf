FROM python:3.4-alpine
RUN apk update
RUN apk add build-base
RUN apk add nodejs
RUN apk add imagemagick
RUN apk add git
RUN pip install virtualenv
RUN virtualenv /opt/serverstf/
WORKDIR /opt/serverstf/
COPY . src/
RUN ls -l src/
RUN /opt/serverstf/bin/pip install -e src/
RUN cd src/ && npm install
RUN . bin/activate && cd src/ && node_modules/.bin/bower \
    install \
    --allow-root \
    --config.interactive=false
RUN . bin/activate && cd src/ && node_modules/.bin/grunt
RUN cd src/ && rm -r node_modules/
RUN mkdir /opt/geolite2/
WORKDIR /opt/geolite2/
RUN wget http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz
RUN tar xvof GeoLite2-City.tar.gz
RUN mv GeoLite2-City_*/* .
RUN rm -r GeoLite2-City_*

FROM python:3.4-alpine
COPY --from=0 /opt/serverstf/ /opt/serverstf/
COPY --from=0 /opt/geolite2/GeoLite2-City.mmdb /opt/serverstf/
ENTRYPOINT ["/opt/serverstf/bin/serverstf"]
CMD ["--help"]
