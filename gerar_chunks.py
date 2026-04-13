import os
import time
import django

# Carrega as configurações do Django antes de rodar o script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from pypdf import PdfReader
from django.conf import settings
# Voltando para a biblioteca clássica e estável!
import google.generativeai as genai
from Backend.app.documents.models import Documento, ChunkDocumento

genai.configure(api_key=settings.GEMINI_API_KEY)

print("Buscando modelos disponíveis na sua chave da API...")
modelo_embedding = "models/text-embedding-004"
try:
    # Pergunta pro Google quais modelos de embedding a sua chave pode usar
    modelos_disponiveis = [m.name for m in genai.list_models() if 'embedContent' in m.supported_generation_methods]
    if modelos_disponiveis:
        modelo_embedding = modelos_disponiveis[0]
        print(f"✅ Modelo detectado e selecionado automaticamente: {modelo_embedding}")
    else:
        print("❌ ATENÇÃO: Sua chave da API não tem acesso a modelos de embedding!")
except Exception as e:
    print(f"Erro ao listar modelos: {e}")

base_dir = "Documentos"
pastas = ["portarias", "resolucoes", "rod"]

def fatiar_texto(texto, tamanho_chunk=1000, sobreposicao=200):
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + tamanho_chunk
        chunks.append(texto[inicio:fim])
        inicio += tamanho_chunk - sobreposicao
    return chunks

print("Iniciando extração e geração de embeddings em lote...")

for pasta in pastas:
    caminho_pasta = os.path.join(base_dir, pasta)
    if not os.path.exists(caminho_pasta): 
        continue
    
    for arquivo in os.listdir(caminho_pasta):
        if not arquivo.lower().endswith(".pdf"): 
            continue
        
        nome_doc = arquivo.replace(".pdf", "")
        doc = Documento.objects.filter(nome=nome_doc).first()
        
        if not doc:
            continue
            
        if ChunkDocumento.objects.filter(documento=doc).exists():
            continue

        print(f"Processando: {arquivo}...")
        caminho_completo = os.path.join(caminho_pasta, arquivo)
        
        try:
            reader = PdfReader(caminho_completo)
            texto_completo = ""
            for page in reader.pages:
                texto = page.extract_text()
                if texto:
                    texto_completo += texto + "\n"
            
            pedacos = fatiar_texto(texto_completo)
            pedacos_validos = [p for p in pedacos if len(p.strip()) >= 10]
            
            if not pedacos_validos:
                continue
                
            # Chamada usando a biblioteca clássica que não dá erro 404
            result = genai.embed_content(
                model=modelo_embedding,
                content=pedacos_validos
            )
            
            embeddings = result['embedding']
            
            for i, pedaco in enumerate(pedacos_validos):
                ChunkDocumento.objects.create(
                    documento=doc,
                    numero_chunk=i+1,
                    conteudo=pedaco,
                    embedding=embeddings[i]
                )
                
            print(f"✅ {len(pedacos_validos)} chunks criados para {arquivo}")
            
            # Pausa de 2 segundinhos para a API gratuita do Google não bloquear a gente
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Erro em {arquivo}: {e}")

print("--- Processo Finalizado! ---")
print(f"Total de Chunks no banco: {ChunkDocumento.objects.count()}")