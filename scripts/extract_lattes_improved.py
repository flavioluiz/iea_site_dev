#!/usr/bin/env python3
"""
Extração MELHORADA de Dados do Lattes
- Extração corrigida de métricas (WoS h-index, etc.)
- Extração de publicações em lotes via LLM
- Usa API da Synthetic ao invés do Gemini CLI
"""

import json
import re
import os
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from PIL import Image
from io import BytesIO
import argparse
from datetime import datetime


class LattesExtractorImproved:
    def __init__(self, html_dir, output_dir, profiles_dir, synthetic_api_key=None,
                 skip_existing=False, force=False):
        self.html_dir = Path(html_dir)
        self.output_dir = Path(output_dir)
        self.profiles_dir = Path(profiles_dir)
        self.synthetic_api_key = synthetic_api_key or os.environ.get('SYNTHETIC_API_KEY')
        self.skip_existing = skip_existing
        self.force = force

        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.photos_dir = Path("../static/images/pessoal")
        self.photos_dir.mkdir(exist_ok=True, parents=True)

    def extract_photo_url(self, soup):
        """Extract photo URL from Lattes"""
        foto_tag = soup.find('img', class_='foto')
        if foto_tag and 'src' in foto_tag.attrs:
            return foto_tag['src']
        return None

    def download_and_optimize_photo(self, photo_url, professor_id):
        """Download photo and optimize it"""
        if not photo_url:
            return None

        try:
            # Download photo
            response = requests.get(photo_url, timeout=10)
            response.raise_for_status()

            # Open with PIL
            img = Image.open(BytesIO(response.content))

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background

            # Resize to max 400x400 maintaining aspect ratio
            max_size = (400, 400)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save as JPEG with optimization
            output_path = self.photos_dir / f"{professor_id}.jpg"
            img.save(output_path, 'JPEG', quality=85, optimize=True)

            print(f"  ✓ Foto salva: {output_path} ({os.path.getsize(output_path) // 1024}KB)")
            return f"{professor_id}.jpg"

        except Exception as e:
            print(f"  ✗ Erro ao baixar foto: {e}")
            return None

    def extract_orcid(self, soup):
        """Extract ORCID ID"""
        orcid_link = soup.find('a', href=re.compile(r'orcid\.org'))
        if orcid_link:
            return orcid_link['href']
        return ""

    def extract_citations_data_improved(self, soup):
        """
        Extração MELHORADA de dados de citação
        Corrige problemas com Web of Science h-index
        """
        citations = {
            'web_of_science': {'link': '', 'works': 0, 'citations': 0, 'h_index': 0},
            'scopus': {'link': '', 'works': 0, 'citations': 0, 'h_index': 0},
            'scielo': {'link': '', 'works': 0, 'citations': 0},
            'google_scholar': {'link': '', 'works': 0, 'citations': 0}
        }

        # Busca todos os containers de ciências
        science_containers = soup.find_all('div', class_='science_cont')

        for container in science_containers:
            # Identifica qual plataforma
            web_s_div = container.find('div', class_='web_s')
            if not web_s_div:
                continue

            platform_text = web_s_div.get_text()

            if 'Web of Science' in platform_text:
                # Link do ResearcherID
                researcher_link = web_s_div.find('a', href=True)
                if researcher_link:
                    citations['web_of_science']['link'] = researcher_link['href']

                # Total de trabalhos
                trab_div = container.find('div', class_='trab')
                if trab_div:
                    match = re.search(r'(\d+)', trab_div.get_text())
                    if match:
                        citations['web_of_science']['works'] = int(match.group(1))

                # Citações
                cita_div = container.find('div', class_='cita')
                if cita_div:
                    match = re.search(r'(\d+)', cita_div.get_text())
                    if match:
                        citations['web_of_science']['citations'] = int(match.group(1))

                # Fator H
                fator_div = container.find('div', class_='fator')
                if fator_div:
                    match = re.search(r'(\d+)', fator_div.get_text())
                    if match:
                        citations['web_of_science']['h_index'] = int(match.group(1))

            elif 'SCOPUS' in platform_text:
                # Total de trabalhos
                trab_div = container.find('div', class_='trab')
                if trab_div:
                    match = re.search(r'(\d+)', trab_div.get_text())
                    if match:
                        citations['scopus']['works'] = int(match.group(1))

                # Citações
                cita_div = container.find('div', class_='cita')
                if cita_div:
                    match = re.search(r'(\d+)', cita_div.get_text())
                    if match:
                        citations['scopus']['citations'] = int(match.group(1))

                # Fator H (se disponível)
                fator_div = container.find('div', class_='fator')
                if fator_div:
                    match = re.search(r'(\d+)', fator_div.get_text())
                    if match:
                        citations['scopus']['h_index'] = int(match.group(1))

            elif 'SciELO' in platform_text:
                trab_div = container.find('div', class_='trab')
                if trab_div:
                    match = re.search(r'(\d+)', trab_div.get_text())
                    if match:
                        citations['scielo']['works'] = int(match.group(1))

                cita_div = container.find('div', class_='cita')
                if cita_div:
                    match = re.search(r'(\d+)', cita_div.get_text())
                    if match:
                        citations['scielo']['citations'] = int(match.group(1))

            elif 'Google Scholar' in platform_text:
                trab_div = container.find('div', class_='trab')
                if trab_div:
                    match = re.search(r'(\d+)', trab_div.get_text())
                    if match:
                        citations['google_scholar']['works'] = int(match.group(1))

                cita_div = container.find('div', class_='cita')
                if cita_div:
                    match = re.search(r'(\d+)', cita_div.get_text())
                    if match:
                        citations['google_scholar']['citations'] = int(match.group(1))

                # Link do Google Scholar
                detalhes_div = container.find('div', class_='detalhes')
                if detalhes_div:
                    text = detalhes_div.get_text().strip()
                    if 'scholar.google' in text:
                        citations['google_scholar']['link'] = text

        return citations

    def check_cnpq_fellowship(self, soup):
        """Check if professor is CNPq productivity fellow"""
        text = soup.get_text()
        patterns = [
            r'Bolsista.*Produtividade.*CNPq',
            r'CNPq.*Produtividade',
            r'Productivity.*Fellow.*CNPq'
        ]

        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Try to extract level
                level_match = re.search(r'(1[A-D]|2|PQ-?[12])', text)
                if level_match:
                    return f"Sim - Nível {level_match.group(1)}"
                return "Sim"

        return "Não"

    def extract_articles_batch(self, soup, batch_size=10):
        """
        Extrai artigos em lotes usando BeautifulSoup
        Identifica as divs 'artigo-completo' e agrupa em lotes
        """
        # Encontra todos os artigos
        article_divs = soup.find_all('div', class_='artigo-completo')

        if not article_divs:
            print(f"  ⚠ Nenhum artigo encontrado")
            return []

        print(f"  📚 {len(article_divs)} artigos encontrados, extraindo em lotes de {batch_size}...")

        all_articles = []

        # Processa em lotes
        for i in range(0, len(article_divs), batch_size):
            batch = article_divs[i:i+batch_size]
            batch_articles = []

            for article_div in batch:
                try:
                    article_data = self._parse_article_html(article_div)
                    if article_data:
                        batch_articles.append(article_data)
                except Exception as e:
                    print(f"    ✗ Erro ao parsear artigo: {e}")
                    continue

            if self.synthetic_api_key and batch_articles:
                # Envia lote para LLM para enriquecer/validar
                enriched = self._enrich_articles_with_llm(batch_articles, i//batch_size + 1)
                all_articles.extend(enriched)
            else:
                all_articles.extend(batch_articles)

            print(f"    ✓ Lote {i//batch_size + 1}/{(len(article_divs)-1)//batch_size + 1} processado ({len(batch_articles)} artigos)")

        return all_articles

    def _parse_article_html(self, article_div):
        """Parse um artigo individual do HTML"""
        try:
            # Extrai o conteúdo do span transform
            transform_span = article_div.find('span', class_='transform')
            if not transform_span:
                return None

            full_text = transform_span.get_text(' ', strip=True)

            # Extrai DOI
            doi_link = article_div.find('a', class_='icone-doi')
            doi = doi_link['href'].replace('http://dx.doi.org/', '') if doi_link and 'href' in doi_link.attrs else ''

            # Extrai ano
            ano_span = transform_span.find('span', attrs={'data-tipo-ordenacao': 'ano'})
            ano = int(ano_span.get_text()) if ano_span else 0

            # Extrai citações Web of Science e Scopus
            citations_wos = 0
            citations_scopus = 0

            citacao_spans = article_div.find_all('span', class_='numero-citacao')
            for citacao_span in citacao_spans:
                tipo_ord = citacao_span.get('data-tipo-ordenacao', '')
                if tipo_ord == '1':  # Web of Science
                    try:
                        citations_wos = int(citacao_span.get_text())
                    except:
                        pass
                elif tipo_ord == '3':  # Scopus
                    try:
                        citations_scopus = int(citacao_span.get_text())
                    except:
                        pass

            # Tenta extrair título e periódico por padrões
            # Formato: "AUTORES . Título . PERIÓDICO , v. X, p. Y, ANO"
            parts = full_text.split(' . ')
            if len(parts) >= 3:
                titulo = parts[-2].strip()
                periodico_part = parts[-1].split(',')[0].strip()
            else:
                titulo = full_text[:200]  # Fallback
                periodico_part = ""

            return {
                'doi': doi,
                'titulo': titulo,
                'periodico': periodico_part,
                'ano': ano,
                'citations_wos': citations_wos,
                'citations_scopus': citations_scopus,
                'full_text': full_text[:500]  # Primeiros 500 chars
            }

        except Exception as e:
            print(f"      ✗ Erro ao parsear artigo: {e}")
            return None

    def _enrich_articles_with_llm(self, articles, batch_num):
        """
        Envia lote de artigos para LLM para extração/validação de campos
        """
        if not self.synthetic_api_key:
            return articles

        try:
            # Prepara prompt
            prompt = f"""Analise os seguintes {len(articles)} artigos científicos extraídos do Lattes e forneça uma versão estruturada em JSON.

Para cada artigo, extraia:
- autores: lista de autores (todos)
- titulo: título completo do artigo
- periodico: nome do periódico/journal
- ano: ano de publicação
- volume: volume (se disponível)
- paginas: páginas (se disponível)
- doi: DOI (se disponível)

Artigos:
"""
            for idx, art in enumerate(articles, 1):
                prompt += f"\n{idx}. {art['full_text']}\n"

            prompt += """

Retorne APENAS um JSON array com os artigos estruturados:
[
  {
    "autores": ["Autor1", "Autor2", ...],
    "titulo": "...",
    "periodico": "...",
    "ano": 2024,
    "volume": "X",
    "paginas": "Y-Z",
    "doi": "..."
  },
  ...
]"""

            # Chama API Synthetic
            response = requests.post(
                'https://api.synthetic.new/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {self.synthetic_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'hf:Qwen/Qwen3-235B-A22B-Instruct-2507',
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.1,
                    'max_tokens': 4000
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']

                # Extrai JSON da resposta
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    enriched = json.loads(json_match.group(0))

                    # Mescla com dados originais (mantém citações, DOI original se LLM não achou)
                    for i, article in enumerate(articles):
                        if i < len(enriched):
                            article.update(enriched[i])
                            # Mantém citações originais
                            enriched[i]['citations_wos'] = article.get('citations_wos', 0)
                            enriched[i]['citations_scopus'] = article.get('citations_scopus', 0)

                    print(f"      ✓ Lote {batch_num} enriquecido pela LLM")
                    return enriched

        except Exception as e:
            print(f"      ⚠ Erro ao enriquecer com LLM: {e}")

        return articles

    def extract_from_html(self, html_file, professor_id):
        """Extract all data from HTML file"""
        print(f"\n📄 Processando: {html_file.name}")

        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # Load existing profile data
        profile_file = self.profiles_dir / f"{professor_id}.json"
        with open(profile_file, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)

        professor_name = profile_data['nome']

        # Extract basic data
        data = {
            'professor_id': professor_id,
            'professor_name': professor_name,
            'extraction_date': datetime.now().isoformat(),
            'foto': None,
            'orcid': '',
            'citations': {},
            'bolsista_produtividade': 'Não',
            'publications': {
                'artigos_periodicos': []
            }
        }

        # Extract photo
        photo_url = self.extract_photo_url(soup)
        if photo_url:
            data['foto'] = self.download_and_optimize_photo(photo_url, professor_id)

        # Extract ORCID
        data['orcid'] = self.extract_orcid(soup)

        # Extract citations data (IMPROVED)
        data['citations'] = self.extract_citations_data_improved(soup)

        # Check CNPq fellowship
        data['bolsista_produtividade'] = self.check_cnpq_fellowship(soup)

        # Extract articles in batches
        articles = self.extract_articles_batch(soup, batch_size=10)
        data['publications']['artigos_periodicos'] = articles

        return data

    def save_extraction(self, data, professor_id):
        """Save extracted data"""
        output_file = self.output_dir / f"{professor_id}_extracted.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Dados salvos: {output_file}")

    def run(self, limit=None):
        """Run extraction for all HTML files"""
        html_files = sorted(self.html_dir.glob('*.html'))

        if limit:
            html_files = html_files[:limit]

        total = len(html_files)
        print(f"\n{'='*80}")
        print(f"EXTRAÇÃO MELHORADA DE DADOS DO LATTES")
        print(f"{'='*80}")
        print(f"Total de arquivos: {total}")
        print(f"Diretório HTML: {self.html_dir}")
        print(f"Diretório saída: {self.output_dir}")
        print(f"API Synthetic: {'✓ Configurada' if self.synthetic_api_key else '✗ Não configurada'}")
        if self.skip_existing:
            print(f"Modo: ⏭️  Pular arquivos já extraídos")
        elif self.force:
            print(f"Modo: 🔄 Forçar reprocessamento de todos")
        else:
            print(f"Modo: ❓ Perguntar para cada arquivo já extraído")
        print(f"{'='*80}")

        extracted_count = 0
        skipped_count = 0
        errors = []

        for idx, html_file in enumerate(html_files, 1):
            professor_id = html_file.stem
            output_file = self.output_dir / f"{professor_id}_extracted.json"

            # Check if already extracted
            already_exists = output_file.exists()

            print(f"\n[{idx}/{total}] {professor_id}", end='')

            if already_exists and not self.force:
                # File already exists
                if self.skip_existing:
                    print(f" - ⏭️  Já extraído, pulando...")
                    skipped_count += 1
                    continue
                else:
                    # Ask user
                    print(f" - ⚠️  Já extraído!")
                    response = input(f"    Reprocessar? (s/N): ").strip().lower()
                    if response not in ['s', 'sim', 'y', 'yes']:
                        print(f"    ⏭️  Pulando...")
                        skipped_count += 1
                        continue
                    print(f"    🔄 Reprocessando...")
            elif already_exists and self.force:
                print(f" - 🔄 Reprocessando (--force)...")
            else:
                print()

            try:
                data = self.extract_from_html(html_file, professor_id)
                self.save_extraction(data, professor_id)
                extracted_count += 1

                # Summary
                print(f"  📊 Resumo:")
                print(f"     - Artigos: {len(data['publications']['artigos_periodicos'])}")
                print(f"     - H-index (WoS): {data['citations']['web_of_science']['h_index']}")
                print(f"     - H-index (Scopus): {data['citations']['scopus']['h_index']}")
                print(f"     - Citações: {data['citations']['google_scholar']['citations']}")
                print(f"     - Bolsista CNPq: {data['bolsista_produtividade']}")

            except Exception as e:
                print(f"  ✗ ERRO: {e}")
                errors.append((professor_id, str(e)))

        # Summary
        print(f"\n{'='*80}")
        print(f"RESUMO")
        print(f"{'='*80}")
        print(f"✓ Extraídos com sucesso: {extracted_count}")
        print(f"⏭️  Pulados (já extraídos): {skipped_count}")
        print(f"✗ Erros: {len(errors)}")
        if errors:
            print(f"\nErros:")
            for prof_id, error in errors:
                print(f"  - {prof_id}: {error}")
        print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Extrai dados dos HTMLs do Lattes (versão melhorada)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:

  # Extrair todos, perguntando para cada já extraído
  python3 extract_lattes_improved.py

  # Pular automaticamente arquivos já extraídos (RECOMENDADO para LLM)
  python3 extract_lattes_improved.py --skip-existing

  # Forçar reprocessamento de todos
  python3 extract_lattes_improved.py --force

  # Extrair apenas os primeiros 5 (teste)
  python3 extract_lattes_improved.py --limit 5 --skip-existing
        ''')

    parser.add_argument('--html-dir', type=str,
                        default='../../lattes_data/lattes_html',
                        help='Diretório com HTMLs do Lattes')

    parser.add_argument('--output-dir', type=str,
                        default='../../lattes_data/lattes_extracted',
                        help='Diretório para salvar dados extraídos')

    parser.add_argument('--profiles-dir', type=str,
                        default='../data/pessoal/profiles',
                        help='Diretório com perfis JSON')

    parser.add_argument('--synthetic-api-key', type=str,
                        help='Chave da API Synthetic (ou use variável SYNTHETIC_API_KEY)')

    parser.add_argument('--limit', type=int,
                        help='Limitar número de arquivos para teste')

    parser.add_argument('--skip-existing', action='store_true',
                        help='Pular automaticamente arquivos já extraídos (não pergunta)')

    parser.add_argument('--force', action='store_true',
                        help='Forçar reprocessamento de todos os arquivos')

    args = parser.parse_args()

    # Validação: --skip-existing e --force são mutuamente exclusivos
    if args.skip_existing and args.force:
        parser.error("--skip-existing e --force não podem ser usados juntos")

    script_dir = Path(__file__).parent
    html_dir = (script_dir / args.html_dir).resolve()
    output_dir = (script_dir / args.output_dir).resolve()
    profiles_dir = (script_dir / args.profiles_dir).resolve()

    extractor = LattesExtractorImproved(
        html_dir=html_dir,
        output_dir=output_dir,
        profiles_dir=profiles_dir,
        synthetic_api_key=args.synthetic_api_key,
        skip_existing=args.skip_existing,
        force=args.force
    )

    extractor.run(limit=args.limit)


if __name__ == '__main__':
    main()
