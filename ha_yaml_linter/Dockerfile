FROM alpine:3.19

# Install Python and dependencies directly via Alpine apk
RUN apk add --no-cache \
    python3 \
    py3-flask \
    py3-ruamel.yaml

WORKDIR /app

# Copy source files
COPY src/ ./src/
COPY web/ ./web/

# Expose port and run server
EXPOSE 5000
CMD ["python3", "-m", "src.server"]
