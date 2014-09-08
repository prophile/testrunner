FROM ubuntu:12.04
MAINTAINER Alistair Lynn <arplynn@gmail.com>

# Basic ubuntu packages
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get install -y build-essential && \
    apt-get install -y software-properties-common && \
    apt-get install -y byobu curl git htop man unzip vim wget && \
    rm -rf /var/lib/apt/lists/*

ENV HOME /root

# Install Ruby
RUN apt-get install -y ruby ruby-dev ruby-bundler && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /data

# Install travis-cli
RUN gem install travis --no-rdoc --no-ri

# Install travis-build
RUN git clone https://github.com/travis-ci/travis-build.git /opt/travis-build
RUN mkdir /root/.travis
RUN ln -s /opt/travis-build $HOME/.travis/travis-build

RUN travis version

# Install Python packages for testing
RUN apt-get -y install python-pip
RUN apt-get -y install python-virtualenv
RUN mkdir ~/virtualenv
RUN virtualenv -p python2.7 ~/virtualenv/2.7
RUN virtualenv -p python3.4 ~/virtualenv/3.4

ENTRYPOINT ["travis", "run", "--skip-version-check", "--skip-completion-check"]
CMD ["-p"]

