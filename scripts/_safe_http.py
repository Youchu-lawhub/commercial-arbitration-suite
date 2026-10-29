"""Shared public-HTTPS URL policy for external legal-source retrieval.

Prevents accidental local/private endpoint access, including redirects. Does not
claim to sandbox hostile pages or replace legal source/content validation.
"""
from __future__ import annotations
import ipaddress
import socket
import urllib.parse
import urllib.request

class UnsafeURL(ValueError):
    pass

def validate_public_url(url: str, *, https_only: bool = True, resolver=None) -> str:
    if not isinstance(url, str) or len(url) > 4096 or any(ord(c) < 32 for c in url):
        raise UnsafeURL('Invalid URL')
    p = urllib.parse.urlsplit(url)
    if p.scheme.lower() not in ({'https'} if https_only else {'https', 'http'}):
        raise UnsafeURL('Only public HTTPS URLs are allowed' if https_only else 'Unsupported protocol')
    if not p.hostname or p.username is not None or p.password is not None or p.fragment:
        raise UnsafeURL('URL must contain a host, with no credentials or fragment')
    try:
        port = p.port
    except ValueError as e:
        raise UnsafeURL('Invalid port') from e
    if port not in (None, 443 if https_only else 80, 443):
        raise UnsafeURL('Nonstandard ports are blocked')
    host = p.hostname.rstrip('.').lower()
    if not host or host == 'localhost' or host.endswith(('.localhost', '.local', '.internal', '.test', '.invalid')):
        raise UnsafeURL('Local or special-use hostname blocked')
    try:
        ip = ipaddress.ip_address(host.strip('[]'))
        ips = [ip]
    except ValueError:
        if '.' not in host:
            raise UnsafeURL('Single-label hostname blocked')
        lookup = resolver or socket.getaddrinfo
        try:
            records = lookup(host, port or (443 if p.scheme == 'https' else 80), type=socket.SOCK_STREAM)
            ips = [ipaddress.ip_address(info[4][0]) for info in records]
        except (OSError, ValueError) as e:
            raise UnsafeURL('Cannot safely resolve hostname') from e
    if not ips or any(not ip.is_global for ip in ips):
        raise UnsafeURL('Non-public IP address blocked')
    return url

class PublicRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def public_urlopen(req, *, timeout=15, context=None):
    url = req.full_url if isinstance(req, urllib.request.Request) else req
    validate_public_url(url)
    handlers = [PublicRedirectHandler()]
    if context is not None:
        handlers.append(urllib.request.HTTPSHandler(context=context))
    return urllib.request.build_opener(*handlers).open(req, timeout=timeout)
