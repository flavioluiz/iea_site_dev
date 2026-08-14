#!/usr/bin/env python3
"""
Extração de Dados do Lattes com LLM
Extrai informações estruturadas dos HTMLs do Lattes baixados
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


class LattesExtractor:
    def __init__(self, html_dir, output_dir, profiles_dir, use_llm=True):
        self.html_dir = Path(html_dir)
        self.output_dir = Path(output_dir)
        self.profiles_dir = Path(profiles_dir)
        self.use_llm = use_llm

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

    def extract_citations_data(self, soup):
        """Extract citation data from Web of Science, Scopus, SciELO, Google Scholar"""
        citations = {
            'web_of_science': {'link': '', 'works': 0, 'citations': 0, 'h_index': 0},
            'scopus': {'link': '', 'works': 0, 'citations': 0},
            'scielo': {'link': '', 'works': 0, 'citations': 0},
            'google_scholar': {'link': '', 'works': 0, 'citations': 0}
        }

        # Web of Science
        wos_section = soup.find('div', class_='web_s', string=re.compile('Web of Science'))
        if wos_section:
            parent = wos_section.parent
            wos_link = parent.find('a', href=re.compile('researcherid'))
            if wos_link:
                citations['web_of_science']['link'] = wos_link['href']

            works = parent.find('div', class_='trab')
            if works:
                match = re.search(r'(\d+)', works.text)
                if match:
                    citations['web_of_science']['works'] = int(match.group(1))

            cites = parent.find('div', class_='cita')
            if cites:
                match = re.search(r'(\d+)', cites.text)
                if match:
                    citations['web_of_science']['citations'] = int(match.group(1))

            h_factor = parent.find('div', class_='fator')
            if h_factor:
                match = re.search(r'(\d+)', h_factor.text)
                if match:
                    citations['web_of_science']['h_index'] = int(match.group(1))

        # Scopus
        scopus_section = soup.find('div', class_='web_s', string='SCOPUS')
        if scopus_section:
            parent = scopus_section.parent
            works = parent.find('div', class_='trab')
            if works:
                match = re.search(r'(\d+)', works.text)
                if match:
                    citations['scopus']['works'] = int(match.group(1))

            cites = parent.find('div', class_='cita')
            if cites:
                match = re.search(r'(\d+)', cites.text)
                if match:
                    citations['scopus']['citations'] = int(match.group(1))

        # SciELO
        scielo_section = soup.find('div', class_='web_s', string='SciELO')
        if scielo_section:
            parent = scielo_section.parent
            works = parent.find('div', class_='trab')
            if works:
                match = re.search(r'(\d+)', works.text)
                if match:
                    citations['scielo']['works'] = int(match.group(1))

            cites = parent.find('div', class_='cita')
            if cites:
                match = re.search(r'(\d+)', cites.text)
                if match:
                    citations['scielo']['citations'] = int(match.group(1))

        # Google Scholar
        scholar_section = soup.find('div', class_='web_s', string='Google Scholar')
        if scholar_section:
            parent = scholar_section.parent
            works = parent.find('div', class_='trab')
            if works:
                match = re.search(r'(\d+)', works.text)
                if match:
                    citations['google_scholar']['works'] = int(match.group(1))

            cites = parent.find('div', class_='cita')
            if cites:
                match = re.search(r'(\d+)', cites.text)
                if match:
                    citations['google_scholar']['citations'] = int(match.group(1))

            details = parent.find('div', class_='detalhes')
            if details and 'scholar.google' in details.text:
                citations['google_scholar']['link'] = details.text.strip()

        return citations

    def check_cnpq_fellowship(self, soup):
        """Check if professor is CNPq productivity fellow"""
        # Buscar por "Bolsista de Produtividade" ou similar
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

    def extract_with_gemini(self, html_content, professor_name):
        """Extract publications using Gemini LLM"""
        if not self.use_llm:
            return None

        # Save temp HTML file
        temp_file = self.output_dir / f"temp_{professor_name}.html"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        prompt = f"""Analise o currículo Lattes em HTML e extraia as seguintes informações em formato JSON:

1. "bolsista_produtividade": Se o professor é bolsista de produtividade CNPq (Sim/Não e nível se disponível)

2. "artigos_periodicos": Lista de artigos completos publicados em periódicos. Para cada artigo:
   - autores: lista de autores
   - titulo: título do artigo
   - periodico: nome do periódico
   - ano: ano de publicação
   - volume: volume (se disponível)
   - paginas: páginas (se disponível)

3. "livros": Lista de livros publicados/organizados. Para cada livro:
   - autores: lista de autores/organizadores
   - titulo: título do livro
   - ano: ano
   - editora: editora (se disponível)

4. "capitulos_livros": Lista de capítulos de livros. Para cada capítulo:
   - autores: lista de autores
   - titulo: título do capítulo
   - livro: título do livro
   - ano: ano

5. "trabalhos_congressos": Lista de trabalhos completos em anais de congressos. Para cada trabalho:
   - autores: lista de autores
   - titulo: título
   - congresso: nome do congresso
   - ano: ano

IMPORTANTE:
- Extraia TODOS os itens de cada categoria
- Se não houver itens em uma categoria, retorne lista vazia []
- Mantenha a ordem cronológica (mais recentes primeiro)
- Retorne APENAS o JSON, sem texto adicional
- Limite a 30 itens mais recentes por categoria

Formato de saída esperado:
{{
  "bolsista_produtividade": "Sim - Nível 1D" ou "Não",
  "artigos_periodicos": [...]
  "livros": [...],
  "capitulos_livros": [...],
  "trabalhos_congressos": [...]
}}"""

        try:
            # Call Gemini via gemini command in one-shot mode
            # Pass HTML file content via stdin and prompt as positional arg
            with open(temp_file, 'r', encoding='utf-8') as f:
                html_content_str = f.read()

            result = subprocess.run(
                ['gemini', prompt],
                input=html_content_str,
                capture_output=True,
                text=True,
                timeout=180  # Increase timeout for large files
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                # Extract JSON from output
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    temp_file.unlink()  # Delete temp file
                    return data
                else:
                    print(f"  ⚠ No JSON found in Gemini output for {professor_name}")
                    print(f"  Output preview: {output[:200]}")
            else:
                print(f"  ⚠ Gemini command failed with return code {result.returncode}")
                print(f"  Error: {result.stderr[:200]}")

            temp_file.unlink()
            return None

        except Exception as e:
            print(f"  ✗ Erro ao usar Gemini: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return None

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
                'artigos_periodicos': [],
                'livros': [],
                'capitulos_livros': [],
                'trabalhos_congressos': []
            }
        }

        # Extract photo
        photo_url = self.extract_photo_url(soup)
        if photo_url:
            data['foto'] = self.download_and_optimize_photo(photo_url, professor_id)

        # Extract ORCID
        data['orcid'] = self.extract_orcid(soup)

        # Extract citations data
        data['citations'] = self.extract_citations_data(soup)

        # Check CNPq fellowship
        data['bolsista_produtividade'] = self.check_cnpq_fellowship(soup)

        # Extract publications with LLM
        if self.use_llm:
            print(f"  🤖 Extraindo publicações com Gemini...")
            llm_data = self.extract_with_gemini(html_content, professor_id)
            if llm_data:
                if 'bolsista_produtividade' in llm_data:
                    data['bolsista_produtividade'] = llm_data['bolsista_produtividade']

                if 'artigos_periodicos' in llm_data:
                    data['publications']['artigos_periodicos'] = llm_data['artigos_periodicos']
                if 'livros' in llm_data:
                    data['publications']['livros'] = llm_data['livros']
                if 'capitulos_livros' in llm_data:
                    data['publications']['capitulos_livros'] = llm_data['capitulos_livros']
                if 'trabalhos_congressos' in llm_data:
                    data['publications']['trabalhos_congressos'] = llm_data['trabalhos_congressos']

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
        print(f"EXTRAÇÃO DE DADOS DO LATTES")
        print(f"{'='*80}")
        print(f"Total de arquivos: {total}")
        print(f"Diretório HTML: {self.html_dir}")
        print(f"Diretório saída: {self.output_dir}")
        print(f"Usar LLM: {self.use_llm}")
        print(f"{'='*80}")

        extracted_count = 0
        errors = []

        for idx, html_file in enumerate(html_files, 1):
            professor_id = html_file.stem

            print(f"\n[{idx}/{total}] {professor_id}")

            try:
                data = self.extract_from_html(html_file, professor_id)
                self.save_extraction(data, professor_id)
                extracted_count += 1

            except Exception as e:
                print(f"  ✗ ERRO: {e}")
                errors.append((professor_id, str(e)))

        # Summary
        print(f"\n{'='*80}")
        print(f"RESUMO")
        print(f"{'='*80}")
        print(f"✓ Extraídos com sucesso: {extracted_count}")
        print(f"✗ Erros: {len(errors)}")
        if errors:
            print(f"\nErros:")
            for prof_id, error in errors:
                print(f"  - {prof_id}: {error}")
        print(f"{'='*80}")


def main():
    parser = argparse.ArgumentParser(description='Extrai dados dos HTMLs do Lattes')

    parser.add_argument('--html-dir', type=str,
                        default='../../lattes_data/lattes_html',
                        help='Diretório com HTMLs do Lattes')

    parser.add_argument('--output-dir', type=str,
                        default='../../lattes_data/lattes_extracted',
                        help='Diretório para salvar dados extraídos')

    parser.add_argument('--profiles-dir', type=str,
                        default='../data/pessoal/profiles',
                        help='Diretório com perfis JSON')

    parser.add_argument('--no-llm', action='store_true',
                        help='Não usar LLM para extração (apenas scraping básico)')

    parser.add_argument('--limit', type=int,
                        help='Limitar número de arquivos para teste')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    html_dir = (script_dir / args.html_dir).resolve()
    output_dir = (script_dir / args.output_dir).resolve()
    profiles_dir = (script_dir / args.profiles_dir).resolve()

    extractor = LattesExtractor(
        html_dir=html_dir,
        output_dir=output_dir,
        profiles_dir=profiles_dir,
        use_llm=not args.no_llm
    )

    extractor.run(limit=args.limit)


if __name__ == '__main__':
    main()
