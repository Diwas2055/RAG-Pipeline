# Nginx Configuration

## Basic Setup

The default `nginx.conf` provides:
- Load balancing across multiple API instances
- Rate limiting (60 req/min general, 20 req/min for RAG queries)
- Security headers
- Request logging
- Health check endpoint (no rate limit)

## SSL/TLS Setup

### Option 1: Self-Signed Certificate (Development)

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/CN=localhost"
```

### Option 2: Let's Encrypt (Production)

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Generate certificate
certbot --nginx -d api.example.com

# Auto-renewal (add to crontab)
0 0 * * * certbot renew --quiet
```

## Basic Authentication for Flower

```bash
# Install apache2-utils
apt-get install apache2-utils

# Create password file
htpasswd -c nginx/.htpasswd admin

# Update nginx.conf to add auth_basic directives
```

## Testing Configuration

```bash
# Test nginx configuration
docker run --rm -v $(pwd)/nginx/nginx.conf:/etc/nginx/nginx.conf:ro nginx nginx -t

# Reload nginx
docker exec rag_nginx nginx -s reload
```

## Rate Limiting

Current limits:
- General API: 60 requests/minute (burst: 10)
- RAG queries: 20 requests/minute (burst: 5)

Adjust in `nginx.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
```
