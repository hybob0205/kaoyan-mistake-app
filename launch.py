"""拾错本机服务：提供静态页面，并从本机环境文件安全调用 Agnes API。"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
import os
import re

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / '.env'
DEFAULTS = {
    'AGNES_API_BASE_URL': 'https://api.agnes-ai.cn/v1',
    'AGNES_MODEL': 'agnes-3.0-flash',
    'AGNES_API_KEY': '',
}


def load_settings():
    settings = DEFAULTS.copy()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            settings[key.strip()] = value.strip().strip('"').strip("'")
    settings['AGNES_API_BASE_URL'] = os.environ.get('AGNES_API_BASE_URL', settings['AGNES_API_BASE_URL'])
    settings['AGNES_MODEL'] = os.environ.get('AGNES_MODEL', settings['AGNES_MODEL'])
    settings['AGNES_API_KEY'] = os.environ.get('AGNES_API_KEY', settings['AGNES_API_KEY'])
    return settings


def json_response(handler, status, data):
    body = json.dumps(data, ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type', 'application/json; charset=utf-8')
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            config = load_settings()
            return json_response(self, 200, {
                'configured': bool(config['AGNES_API_KEY'] and config['AGNES_MODEL'] and config['AGNES_API_BASE_URL']),
                'model': config['AGNES_MODEL'] if config['AGNES_API_KEY'] else '',
            })
        path = self.path.split('?', 1)[0]
        if path == '/':
            path = '/index.html'
        file = (ROOT / path.lstrip('/')).resolve()
        if ROOT not in file.parents or not file.is_file() or file.name == '.env':
            self.send_error(404)
            return
        content = file.read_bytes()
        kind = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8','.json':'application/json; charset=utf-8'}.get(file.suffix,'application/octet-stream')
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(content)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path != '/api/analyze':
            self.send_error(404)
            return
        config = load_settings()
        if not config['AGNES_API_KEY']:
            return json_response(self, 503, {'error':'AI 服务没有配置密钥。'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > 15 * 1024 * 1024:
                return json_response(self, 413, {'error':'请求为空或超过 15 MB。'})
            incoming = json.loads(self.rfile.read(length))
            question = str(incoming.get('question') or '')[:20000]
            image = str(incoming.get('image') or '')
            subject = str(incoming.get('subject') or '')[:40]
            module = str(incoming.get('module') or '')[:100]
            user_content = [
                {'type':'text','text':f'科目（已由学习者选定，请勿修改）：{subject}\n模块（如已选定请优先保留）：{module}\n题目文字：{question or "请读取图片中的题目"}\n请识别题目，整理知识点、题型、难度、错因、答案和清晰简短的解析。'}
            ]
            if image.startswith('data:image/'):
                user_content.append({'type':'image_url','image_url':{'url':image}})
            elif image:
                return json_response(self, 400, {'error':'图片格式无效。'})
            base = config['AGNES_API_BASE_URL'].rstrip('/')
            endpoint = base if base.endswith('/chat/completions') else base + '/chat/completions'
            payload = {
                'model':config['AGNES_MODEL'], 'temperature':0.2,
                'response_format':{'type':'json_object'},
                'messages':[
                    {'role':'system','content':'你是严谨的中国考研错题整理助手。只根据给定题目作答，不臆造题目条件。返回单个 JSON 对象，字段：question(识别出的完整题干), module(简短章节), knowledge(知识点，可多个，用中文顿号分隔), type(预设题型名称), difficulty(1基础/2中等/3较难), cause(若无作答信息则留空), answer(若无法判断留空), explanation(中文解析), tags(字符串数组)。题目所属 subject 已由用户选择，不要返回或改写 subject。'},
                    {'role':'user','content':user_content},
                ]
            }
            req = Request(endpoint, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'), headers={'Authorization':'Bearer '+config['AGNES_API_KEY'],'Content-Type':'application/json'}, method='POST')
            with urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode('utf-8'))
            text = result['choices'][0]['message']['content']
            text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip(), flags=re.I)
            analysis = json.loads(text)
            return json_response(self, 200, {'analysis':analysis})
        except HTTPError as exc:
            # Do not reflect upstream request headers or credentials to the browser.
            message = 'AI 服务拒绝了请求，请检查模型配置。' if exc.code in (401,403,404) else f'AI 服务暂不可用（HTTP {exc.code}）。'
            return json_response(self, 502, {'error':message})
        except (URLError, TimeoutError):
            return json_response(self, 502, {'error':'连接 Agnes 服务超时或网络不可用。'})
        except (json.JSONDecodeError, KeyError, IndexError, TypeError):
            return json_response(self, 502, {'error':'AI 返回内容无法解析，请重试或手动补充。'})
        except Exception:
            return json_response(self, 500, {'error':'分析请求失败，请重试；错题本地记录已保留。'})

    def log_message(self, fmt, *args):
        # Keep access logs free of request bodies, headers, and credentials.
        super().log_message(fmt, *args)


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 8788), Handler)
    print('拾错已启动：http://127.0.0.1:8788/\n保持窗口运行；停止请按 Control+C。')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == '__main__':
    main()
