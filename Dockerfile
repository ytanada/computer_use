FROM ubuntu:22.04

# 必要なパッケージのインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    vim \
    curl \
    wget \
    locales \
    gnupg \
    git \
    libglib2.0-0 \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libdrm2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    xdg-utils \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    less \
    x11-apps && \
    locale-gen ja_JP.UTF-8 && \
    update-locale LANG=ja_JP.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=ja_JP.UTF-8 \
    LANGUAGE=ja_JP:ja \
    LC_ALL=ja_JP.UTF-8 \
    CONDA_DIR=/opt/anaconda3 \
    PATH=/opt/anaconda3/bin:$PATH

WORKDIR /opt/app

# Anacondaのインストール
RUN wget --no-check-certificate https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh && \
    sh Anaconda3-2024.06-1-Linux-x86_64.sh -b -p $CONDA_DIR && \
    rm -f Anaconda3-2024.06-1-Linux-x86_64.sh

# Google Chromeのインストール
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
    | gpg --dearmor > /etc/apt/trusted.gpg.d/google-chrome.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Python環境の構築
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install --with-deps chromium

# カレントディレクトリに移動
WORKDIR /home/ubuntu/work

# JupyterLab起動（GUIでは不要なら除去可）
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--allow-root", "--LabApp.token=''"]
