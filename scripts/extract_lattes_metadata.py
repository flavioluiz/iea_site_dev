#!/usr/bin/env python3
"""
Extração de Metadados Úteis do Lattes (sem publicações)

Extrai:
- Foto do professor (download e otimização)
- Bolsista CNPq + Nível
- ORCID (apenas se não existir no perfil)
- Formação Acadêmica (doutorado, mestrado, graduação)
- Resumo/Bio
- Prêmios e Títulos
"""

import json
import re
import os
from pathlib import Path
from bs4 import BeautifulSoup
import requests
from PIL import Image
from io import BytesIO
import argparse
from datetime import datetime


class LattesMetadataExtractor:
    def __init__(self, html_dir, output_dir, profiles_dir):
        self.html_dir = Path(html_dir)
        self.output_dir = Path(output_dir)
        self.profiles_dir = Path(profiles_dir)

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

            print(f"  ✓ Foto salva: {output_path.name} ({os.path.getsize(output_path) // 1024}KB)")
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

    def check_cnpq_fellowship(self, soup):
        """
        Check if professor is CNPq productivity fellow
        Returns level if found
        """
        # Buscar no header do currículo
        text = soup.get_text()

        # Padrões para detectar bolsista
        patterns = [
            r'Bolsista de Produtividade em Pesquisa do CNPq\s*-\s*Nível\s+([^\s\n]+)',
            r'Bolsista.*Produtividade.*CNPq.*Nível\s+([^\s\n]+)',
            r'CNPq.*Produtividade.*Nível\s+([^\s\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nivel = match.group(1).strip()
                # Clean up unwanted words that might be extracted
                nivel = re.sub(r'(Endereço|Telefone|Email|Contato).*$', '', nivel, flags=re.IGNORECASE).strip()
                nivel = re.sub(r'\s+', ' ', nivel).strip()  # Remove extra spaces
                if nivel:
                    return f"Sim - Nível {nivel}"

        # Tentar sem nível específico
        if re.search(r'Bolsista.*Produtividade.*CNPq', text, re.IGNORECASE):
            return "Sim"

        return "Não"

    def extract_academic_background(self, soup):
        """
        Extract academic background (PhD, MSc, BSc)
        """
        formations = []

        # Find section "Formação acadêmica/titulação"
        formacao_section = soup.find('a', attrs={'name': 'FormacaoAcademicaTitulacao'})
        if not formacao_section:
            return formations

        # Get parent div with all formations
        parent_div = formacao_section.find_parent('div', class_='title-wrapper')
        if not parent_div:
            return formations

        # Find all formation entries
        data_cells = parent_div.find_all('div', class_='data-cell')

        for cell in data_cells:
            try:
                # Extract period
                period_div = cell.find('div', class_='layout-cell-3')
                if not period_div:
                    continue

                period = period_div.get_text(strip=True)

                # Extract details
                details_div = cell.find('div', class_='layout-cell-9')
                if not details_div:
                    continue

                details_text = details_div.get_text(' ', strip=True)

                # Determine degree type
                degree_type = ""
                if 'Doutorado' in details_text:
                    degree_type = "Doutorado"
                elif 'Mestrado' in details_text:
                    degree_type = "Mestrado"
                elif 'Graduação' in details_text:
                    degree_type = "Graduação"
                elif 'Pós-Doutorado' in details_text or 'Pós Doutorado' in details_text:
                    degree_type = "Pós-Doutorado"
                else:
                    continue

                # Extract institution
                institution = ""
                institution_match = re.search(r'(?:em|in)\s+(.+?)(?:\.|,|\n|<br)', details_text)
                if institution_match:
                    institution = institution_match.group(1).strip()

                # Extract title
                title = ""
                title_match = re.search(r'Título:\s*(.+?)(?:\.|<br|\n)', details_text)
                if title_match:
                    title = title_match.group(1).strip()

                # Extract year
                year_match = re.search(r'Ano de Obtenção:\s*(\d{4})', details_text)
                year = int(year_match.group(1)) if year_match else None

                formation = {
                    "tipo": degree_type,
                    "periodo": period,
                    "instituicao": institution,
                    "titulo": title,
                    "ano_obtencao": year
                }

                formations.append(formation)

            except Exception as e:
                print(f"    ⚠ Erro ao parsear formação: {e}")
                continue

        return formations

    def extract_resume(self, soup):
        """Extract resume/bio text"""
        resumo_p = soup.find('p', class_='resumo')
        if resumo_p:
            # Remove "Texto informado pelo autor"
            text = resumo_p.get_text(strip=True)
            text = re.sub(r'\(Texto informado pelo autor\)', '', text, flags=re.IGNORECASE)
            return text.strip()
        return ""

    def extract_awards(self, soup):
        """Extract awards and titles"""
        awards = []

        # Find section "Prêmios e títulos"
        awards_section = soup.find('a', attrs={'name': 'PremiosTitulos'})
        if not awards_section:
            return awards

        # Get parent div
        parent_div = awards_section.find_parent('div', class_='title-wrapper')
        if not parent_div:
            return awards

        # Find all award entries
        data_cells = parent_div.find_all('div', class_='data-cell')

        for cell in data_cells:
            try:
                # Extract year
                year_div = cell.find('div', class_='layout-cell-3')
                if not year_div:
                    continue

                year_text = year_div.get_text(strip=True)
                year = int(year_text) if year_text.isdigit() else year_text

                # Extract award description
                award_div = cell.find('div', class_='layout-cell-9')
                if not award_div:
                    continue

                award_text = award_div.get_text(strip=True)

                if award_text:
                    awards.append({
                        "ano": year,
                        "titulo": award_text
                    })

            except Exception as e:
                print(f"    ⚠ Erro ao parsear prêmio: {e}")
                continue

        return awards

    def extract_languages(self, soup):
        """Extract languages"""
        languages = []

        # Find section "Idiomas"
        lang_section = soup.find('a', attrs={'name': 'Idiomas'})
        if not lang_section:
            return languages

        # Get parent div
        parent_div = lang_section.find_parent('div', class_='title-wrapper')
        if not parent_div:
            return languages

        # Find all language entries
        data_cells = parent_div.find_all('div', class_='data-cell')

        for cell in data_cells:
            try:
                # Extract language name
                lang_div = cell.find('div', class_='layout-cell-3')
                if not lang_div:
                    continue

                lang_name = lang_div.get_text(strip=True)

                # Extract proficiency
                prof_div = cell.find('div', class_='layout-cell-9')
                if not prof_div:
                    continue

                proficiency = prof_div.get_text(strip=True)

                if lang_name:
                    languages.append({
                        "idioma": lang_name,
                        "proficiencia": proficiency
                    })

            except Exception as e:
                print(f"    ⚠ Erro ao parsear idioma: {e}")
                continue

        return languages

    def extract_from_html(self, html_file, professor_id):
        """Extract all metadata from HTML file"""
        print(f"\n📄 Processando: {html_file.name}")

        with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # Load existing profile to check ORCID
        profile_file = self.profiles_dir / f"{professor_id}.json"
        existing_orcid = ""
        if profile_file.exists():
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                # Check if ORCID already exists in links
                existing_orcid = profile_data.get('links', {}).get('orcid', '')

        # Extract metadata
        metadata = {
            'professor_id': professor_id,
            'extraction_date': datetime.now().isoformat(),
            'foto': None,
            'orcid': '',
            'orcid_already_exists': bool(existing_orcid),
            'bolsista_produtividade': 'Não',
            'formacao_academica': [],
            'resumo': '',
            'premios_titulos': [],
            'idiomas': []
        }

        # Extract photo
        photo_url = self.extract_photo_url(soup)
        if photo_url:
            metadata['foto'] = self.download_and_optimize_photo(photo_url, professor_id)
        else:
            print(f"  ⚠ Foto não encontrada")

        # Extract ORCID (only if doesn't exist)
        if not existing_orcid:
            metadata['orcid'] = self.extract_orcid(soup)
            if metadata['orcid']:
                print(f"  ✓ ORCID encontrado: {metadata['orcid']}")
        else:
            print(f"  ⏭️  ORCID já existe no perfil, não sobrescrever")

        # Extract CNPq fellowship
        metadata['bolsista_produtividade'] = self.check_cnpq_fellowship(soup)
        print(f"  ✓ Bolsista CNPq: {metadata['bolsista_produtividade']}")

        # Extract academic background
        metadata['formacao_academica'] = self.extract_academic_background(soup)
        print(f"  ✓ Formações: {len(metadata['formacao_academica'])}")

        # Extract resume
        metadata['resumo'] = self.extract_resume(soup)
        if metadata['resumo']:
            print(f"  ✓ Resumo: {len(metadata['resumo'])} caracteres")

        # Extract awards
        metadata['premios_titulos'] = self.extract_awards(soup)
        print(f"  ✓ Prêmios: {len(metadata['premios_titulos'])}")

        # Extract languages
        metadata['idiomas'] = self.extract_languages(soup)
        print(f"  ✓ Idiomas: {len(metadata['idiomas'])}")

        return metadata

    def save_metadata(self, metadata, professor_id):
        """Save extracted metadata"""
        output_file = self.output_dir / f"{professor_id}_metadata.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Metadados salvos: {output_file.name}")

    def run(self, limit=None):
        """Run extraction for all HTML files"""
        html_files = sorted(self.html_dir.glob('*.html'))

        if limit:
            html_files = html_files[:limit]

        total = len(html_files)
        print(f"\n{'='*80}")
        print(f"EXTRAÇÃO DE METADADOS DO LATTES")
        print(f"{'='*80}")
        print(f"Total de arquivos: {total}")
        print(f"Diretório HTML: {self.html_dir}")
        print(f"Diretório saída: {self.output_dir}")
        print(f"{'='*80}")

        extracted_count = 0
        errors = []

        for idx, html_file in enumerate(html_files, 1):
            professor_id = html_file.stem

            print(f"\n[{idx}/{total}] {professor_id}")

            try:
                metadata = self.extract_from_html(html_file, professor_id)
                self.save_metadata(metadata, professor_id)
                extracted_count += 1

            except Exception as e:
                print(f"  ✗ ERRO: {e}")
                import traceback
                traceback.print_exc()
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
    parser = argparse.ArgumentParser(
        description='Extrai metadados úteis dos HTMLs do Lattes (sem publicações)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Dados extraídos:
  - Foto (download e otimização)
  - Bolsista CNPq + Nível
  - ORCID (apenas se não existir no perfil)
  - Formação Acadêmica
  - Resumo/Bio
  - Prêmios e Títulos
  - Idiomas

Exemplo de uso:
  python3 extract_lattes_metadata.py
  python3 extract_lattes_metadata.py --limit 5
        ''')

    parser.add_argument('--html-dir', type=str,
                        default='../../lattes_data/lattes_html',
                        help='Diretório com HTMLs do Lattes')

    parser.add_argument('--output-dir', type=str,
                        default='../../lattes_data/lattes_metadata',
                        help='Diretório para salvar metadados extraídos')

    parser.add_argument('--profiles-dir', type=str,
                        default='../data/pessoal/profiles',
                        help='Diretório com perfis JSON')

    parser.add_argument('--limit', type=int,
                        help='Limitar número de arquivos para teste')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    html_dir = (script_dir / args.html_dir).resolve()
    output_dir = (script_dir / args.output_dir).resolve()
    profiles_dir = (script_dir / args.profiles_dir).resolve()

    extractor = LattesMetadataExtractor(
        html_dir=html_dir,
        output_dir=output_dir,
        profiles_dir=profiles_dir
    )

    extractor.run(limit=args.limit)


if __name__ == '__main__':
    main()
