FROM ubuntu:14.04
MAINTAINER Javier Ruiz <javier.ruiz.duran@gmail.com>

RUN echo 'APT::Get::Assume-Yes "true";' >> /etc/apt/apt.conf \
    && echo 'APT::Get::force-yes "true";' >> /etc/apt/apt.conf
RUN locale-gen fr_FR \
    && locale-gen en_US.UTF-8 \
    && dpkg-reconfigure locales \
    && update-locale LANG=en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8
RUN ln -s /usr/share/i18n/SUPPORTED /var/lib/locales/supported.d/all \
    && locale-gen
ENV PYTHONIOENCODING utf-8
ENV TERM xterm
#Install Odoo dependencies
RUN apt-get update -q && apt-get upgrade -q && \
    apt-get install --allow-unauthenticated -q \
    wget
RUN echo 'deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main' >> /etc/apt/sources.list.d/pgdg.list && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | \
    sudo apt-key add -
RUN apt-get update -q && apt-get upgrade -q && \
    apt-get install --allow-unauthenticated -q \
    fontconfig \
    libevent-dev \
    libjpeg-dev \
    libldap2-dev \
    libsasl2-dev \
    libx11-6 \
    libxext6 \
    libxml2-dev \
    libxrender1 \
    libxslt-dev \
    nano \
    npm \
    node-less \
    postgresql-server-dev-9.4 \
    python \
    python-dev \
    xfonts-75dpi \
    xfonts-base

# Install wkhtmltopdf
ADD ./deps/wkhtmltox_0.12.5-1.trusty_amd64.deb /tmp/wkhtmltox_0.12.5-1.trusty_amd64.deb
RUN dpkg -i /tmp/wkhtmltox_0.12.5-1.trusty_amd64.deb

# Install nodejs
#RUN ln -s /usr/bin/nodejs /usr/bin/node && \
#    npm config set strict-ssl false && \
#    npm install -g less less-plugin-clean-css

# Install pip
RUN cd /tmp && \
    wget -q https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py

# Download and install odoo requirements from github.com/odoo/odoo/requirements.txt
ADD server/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Cleanup
RUN apt-get clean && rm -rf /var/lib/apt/lists/* && rm -rf /tmp/*

# Add user
RUN adduser --home=/opt/odoo --disabled-password --gecos "" --shell=/bin/bash odoo
RUN echo 'root:odoo' |chpasswd

# Create entrypoint
ADD ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Add Logrotate file
ADD config/logrotate /etc/logrotate.d/odoo-server
RUN chmod 755 /etc/logrotate.d/odoo-server

# Add log directory
RUN mkdir -p /var/log/odoo && \
    chown odoo:root /var/log/odoo

# Add filestorage folder
RUN /bin/bash -c "mkdir -p /home/odoo/filestorage"
RUN chown odoo /home/odoo/filestorage

VOLUME ["/opt/odoo/", "/var/log/odoo", "/home/odoo/filestorage"]

RUN echo $'#!/bin/bash\nchown -R odoo:odoo /opt/odoo && chmod 640 /opt/odoo/config/odoo-server.conf' > /permission.sh && chmod +x /permission.sh
CMD /permission.sh

USER odoo
CMD /entrypoint.sh

EXPOSE 8069
EXPOSE 8072
EXPOSE 22