FROM minio/minio:latest

# MinIO is ready to use from the official image
# The environment variables and start command are passed at runtime by Railway

EXPOSE 9000 9001

# Health check
HEALTHCHECK --interval=30s --timeout=20s --start-period=10s --retries=3 \
  CMD /usr/bin/curl -f http://localhost:9000/minio/health/live || exit 1

# Default command (will be overridden by Railway start command)
CMD ["server", "/data", "--console-address", ":9001"]
