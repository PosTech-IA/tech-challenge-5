FROM minio/minio:latest

# MinIO doesn't require any custom setup
# The environment variables and command are passed at runtime by Railway

EXPOSE 9000 9001

# Health check
HEALTHCHECK --interval=30s --timeout=20s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:9000/minio/health/live || exit 1
