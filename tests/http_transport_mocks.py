"""
HTTPトランスポート外部I/Oモック化設定

タイムアウト問題を解消するための外部依存モック化設定
- JWKS取得のモック化
- 外部HTTPリクエストのモック化
- レート制限チェックのモック化
"""

import json
import time
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from httpx import ASGITransport
from authlib.jose import JsonWebKey, jwt


class HttpTransportMockConfig:
    """HTTPトランスポートのモック化設定"""
    
    def __init__(self):
        self.jwks_response = None
        self.external_http_responses = {}
        self.rate_limit_check_enabled = True
        
    def setup_jwks_mock(self, private_key=None, public_key=None, kid="test-key"):
        """JWKSレスポンスのモック設定"""
        if private_key is None:
            # テスト用RSAキー生成
            private_key = JsonWebKey.generate_key("RSA", 2048, is_private=True)
            
        if public_key is None:
            public_key = JsonWebKey.import_key(private_key.as_dict(is_private=True))
            
        private_jwk = private_key.as_dict(is_private=True)
        private_jwk["kid"] = kid
        public_jwk = public_key.as_dict(is_private=False)
        
        self.jwks_response = {"keys": [public_jwk]}
        return private_jwk, public_jwk
    
    def add_external_response(self, url: str, response_data: Dict[str, Any], status_code: int = 200):
        """外部HTTPレスポンスのモック設定"""
        self.external_http_responses[url] = {
            "data": response_data,
            "status_code": status_code
        }
    
    def disable_rate_limit_check(self):
        """レート制限チェックを無効化"""
        self.rate_limit_check_enabled = False


class MockHttpTransport:
    """HTTPトランスポートのモック実装"""
    
    def __init__(self, config: HttpTransportMockConfig):
        self.config = config
        self.call_count = 0
        self.response_times = []
    
    async def mock_httpx_get(self, url: str, **kwargs) -> httpx.Response:
        """httpx.AsyncClient.getのモック"""
        start_time = time.time()
        self.call_count += 1
        
        # JWKS URLの場合
        if "jwks" in url.lower() or ".well-known/jwks.json" in url:
            if self.config.jwks_response:
                response = MagicMock()
                response.status_code = 200
                response.json = lambda: self.config.jwks_response
                response.text = json.dumps(self.config.jwks_response)
                self.response_times.append(time.time() - start_time)
                return response
        
        # 登録された外部レスポンス
        if url in self.config.external_http_responses:
            mock_data = self.config.external_http_responses[url]
            response = MagicMock()
            response.status_code = mock_data["status_code"]
            response.json = lambda: mock_data["data"]
            response.text = json.dumps(mock_data["data"])
            self.response_times.append(time.time() - start_time)
            return response
        
        # デフォルトレスポンス（タイムアウトを防ぐため即座に返答）
        response = MagicMock()
        response.status_code = 200
        response.json = lambda: {"mocked": True}
        response.text = json.dumps({"mocked": True})
        self.response_times.append(time.time() - start_time)
        return response
    
    def get_average_response_time(self) -> float:
        """平均レスポンスタイムを取得"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_call_stats(self) -> Dict[str, Any]:
        """呼び出し統計を取得"""
        return {
            "total_calls": self.call_count,
            "response_times": self.response_times,
            "average_response_time": self.get_average_response_time(),
            "jwks_calls": len([t for t in self.response_times if t > 0])
        }


def create_transport_mocks() -> tuple[HttpTransportMockConfig, MockHttpTransport]:
    """トランスポートモックの作成"""
    config = HttpTransportMockConfig()
    transport = MockHttpTransport(config)
    return config, transport


def apply_http_transport_mocks(monkeypatch, config: HttpTransportMockConfig, transport: MockHttpTransport):
    """HTTPトランスポートのモックを適用

    注意: ローカルASGIアプリ（テスト対象）への呼び出しはモックしない。
    base_url が `http://test` や `http://127.0.0.1` 等のローカル、
    または `ASGITransport` を使用している場合はオリジナルの httpx 実装を使用する。
    それ以外（外部I/O）はモックで即時応答する。
    """

    # オリジナル関数を保持
    _orig_get = httpx.AsyncClient.get

    def _is_local_client(self, url: str, kwargs: Dict[str, Any]) -> bool:
        try:
            base = getattr(self, "base_url", None)
            base_str = str(base) if base else ""
        except Exception:
            base_str = ""
        is_local_base = base_str.startswith(("http://test", "http://127.0.0.1", "http://localhost"))
        has_asgi_transport = isinstance(kwargs.get("transport") or getattr(self, "_transport", None), ASGITransport)
        is_relative = isinstance(url, str) and url.startswith("/")
        return bool(is_local_base or has_asgi_transport or is_relative)

    async def _guarded_get(self, url: str, **kwargs):
        if _is_local_client(self, url, kwargs):
            # ローカルASGIアプリはオリジナルで実行
            return await _orig_get(self, url, **kwargs)
        # 外部I/Oはモック応答
        return await transport.mock_httpx_get(url, **kwargs)

    # httpx.AsyncClient のメソッドをガード付きに差し替え
    monkeypatch.setattr(httpx.AsyncClient, "get", _guarded_get, raising=False)
    # POST はローカルASGIに影響するためモックしない

    # 外部依存のある関数をモック化（必要に応じて個別に設定）
    # monkeypatch.setattr(
    #     "mcp_agent_mail.auth.jwks_fetch",
    #     AsyncMock(return_value=config.jwks_response),
    #     raising=False
    # )

    return transport


def create_test_jwt_token(private_jwk: Dict[str, Any], payload: Dict[str, Any]) -> str:
    """テスト用JWTトークンを作成"""
    header = {"alg": "RS256", "kid": private_jwk.get("kid", "test-key")}
    token = jwt.encode(header, payload, private_jwk)
    return token.decode("utf-8") if isinstance(token, bytes) else str(token)


# テスト用ヘルパー関数
def setup_http_transport_mocks(monkeypatch, enable_rate_limit: bool = False):
    """HTTPトランスポートのモックをセットアップ"""
    config, transport = create_transport_mocks()
    
    # JWKSモック設定
    private_jwk, _ = config.setup_jwks_mock()
    
    if not enable_rate_limit:
        config.disable_rate_limit_check()
    
    # モック適用
    mock_stats = apply_http_transport_mocks(monkeypatch, config, transport)
    
    return {
        "config": config,
        "transport": transport,
        "private_jwk": private_jwk,
        "mock_stats": mock_stats
    }