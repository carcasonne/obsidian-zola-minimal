FROM python:3.8-alpine

# Install everything for Rust
RUN apk add --update-cache curl gcc musl-dev

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Add .cargo/bin to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Compile and install obsidian-export
# Version is last known to work from here: https://github.com/ppeetteerrs/obsidian-zola/tree/fef8fdc09c0dffa588d5ead6b3f6ccc6bdc78030/bin
RUN cargo install obsidian-export --version 22.1.0

# Install dependencies for obsidian-zola
RUN apk add --update-cache zola git rsync

# Install python packages for obsidian-zola
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
