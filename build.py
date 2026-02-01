#!/usr/bin/env python3
"""
Build Script - LOBINHO-BET
===========================
Gera arquivos estaticos para deploy no Firebase Hosting.
"""

import os
import shutil

# Importa o template do dashboard
from dashboard_local import HTML_TEMPLATE

def build():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   LOBINHO-BET - Build para Firebase                               ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)

    # Criar pasta public se nao existir
    public_dir = os.path.join(os.path.dirname(__file__), 'public')

    if os.path.exists(public_dir):
        shutil.rmtree(public_dir)
        print(f"[OK] Pasta public limpa")

    os.makedirs(public_dir)
    print(f"[OK] Pasta public criada: {public_dir}")

    # Gerar index.html
    index_path = os.path.join(public_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)
    print(f"[OK] index.html gerado")

    # Criar arquivo 404.html (copia do index para SPA)
    error_path = os.path.join(public_dir, '404.html')
    with open(error_path, 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)
    print(f"[OK] 404.html gerado")

    # Criar firebase.json se nao existir
    firebase_json = os.path.join(os.path.dirname(__file__), 'firebase.json')
    if not os.path.exists(firebase_json):
        firebase_config = '''{
  "hosting": {
    "public": "public",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**",
      "**/*.py",
      "**/__pycache__/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.html",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "no-cache"
          }
        ]
      }
    ]
  }
}'''
        with open(firebase_json, 'w', encoding='utf-8') as f:
            f.write(firebase_config)
        print(f"[OK] firebase.json criado")
    else:
        print(f"[--] firebase.json ja existe")

    # Criar .firebaserc se nao existir
    firebaserc = os.path.join(os.path.dirname(__file__), '.firebaserc')
    if not os.path.exists(firebaserc):
        firebaserc_content = '''{
  "projects": {
    "default": "lobinho-bet"
  }
}'''
        with open(firebaserc, 'w', encoding='utf-8') as f:
            f.write(firebaserc_content)
        print(f"[OK] .firebaserc criado (edite o projeto se necessario)")
    else:
        print(f"[--] .firebaserc ja existe")

    print(f"""
═══════════════════════════════════════════════════════════════════
  BUILD CONCLUIDO!
═══════════════════════════════════════════════════════════════════

  Arquivos gerados em: {public_dir}

  Para fazer deploy no Firebase:

  1. Instale Firebase CLI (se ainda nao tem):
     npm install -g firebase-tools

  2. Faca login no Firebase:
     firebase login

  3. Inicialize o projeto (primeira vez):
     firebase init hosting

  4. Faca o deploy:
     firebase deploy --only hosting

  Ou use o comando rapido:
     firebase deploy

═══════════════════════════════════════════════════════════════════
""")


if __name__ == "__main__":
    build()
