#!/usr/bin/env python3
"""
Script para download sistemático de currículos Lattes
Abre cada Lattes, aguarda resolução manual do captcha, e salva o HTML
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import argparse


class LattesDownloader:
    def __init__(self, profiles_dir, output_dir, headless=False):
        self.profiles_dir = Path(profiles_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # Log file to track progress
        self.log_file = self.output_dir / 'download_log.json'
        self.load_log()

        # Setup Chrome driver
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)

    def load_log(self):
        """Load download progress log"""
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.log = json.load(f)
        else:
            self.log = {
                'downloaded': [],
                'failed': [],
                'skipped': [],
                'last_update': None
            }

    def save_log(self):
        """Save download progress log"""
        self.log['last_update'] = datetime.now().isoformat()
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log, f, indent=2, ensure_ascii=False)

    def get_professors(self):
        """Load all professor profiles"""
        professors = []
        for json_file in sorted(self.profiles_dir.glob('*.json')):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data['links']['lattes']:
                    professors.append({
                        'id': data['id'],
                        'nome': data['nome'],
                        'lattes': data['links']['lattes'],
                        'area': data['area']
                    })
        return professors

    def is_downloaded(self, prof_id):
        """Check if professor's Lattes was already downloaded"""
        html_file = self.output_dir / f"{prof_id}.html"
        return html_file.exists() or prof_id in self.log['downloaded']

    def wait_for_user_confirmation(self, prof_name):
        """Wait for user to press Enter after solving captcha"""
        print("\n" + "="*80)
        print(f"👤 Professor: {prof_name}")
        print("="*80)
        print("\n⏳ Aguardando resolução do captcha...")
        print("   1. Resolva o captcha no navegador")
        print("   2. Aguarde a página carregar completamente")
        print("   3. Pressione ENTER quando estiver pronto")
        print("\n   Digite 's' + ENTER para pular este professor")
        print("   Digite 'q' + ENTER para sair")
        print("-"*80)

        response = input("Pressione ENTER para continuar: ").strip().lower()

        if response == 'q':
            return 'quit'
        elif response == 's':
            return 'skip'
        return 'continue'

    def save_page(self, prof_id, prof_name):
        """Save current page HTML"""
        html_file = self.output_dir / f"{prof_id}.html"

        # Get page source
        html_content = self.driver.page_source

        # Save HTML
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Save metadata
        metadata = {
            'professor_id': prof_id,
            'professor_name': prof_name,
            'url': self.driver.current_url,
            'download_date': datetime.now().isoformat(),
            'file_size': len(html_content),
            'success': True
        }

        metadata_file = self.output_dir / f"{prof_id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"✅ Salvo: {html_file} ({len(html_content):,} bytes)")
        return True

    def download_lattes(self, prof):
        """Download a single Lattes curriculum"""
        prof_id = prof['id']
        prof_name = prof['nome']
        lattes_url = prof['lattes']

        print(f"\n🌐 Abrindo: {lattes_url}")

        try:
            # Open Lattes page
            self.driver.get(lattes_url)

            # Wait a bit for page to load
            time.sleep(2)

            # Wait for user to solve captcha
            action = self.wait_for_user_confirmation(prof_name)

            if action == 'quit':
                return 'quit'
            elif action == 'skip':
                self.log['skipped'].append(prof_id)
                print(f"⏭️  Pulado: {prof_name}")
                return 'skip'

            # Save the page
            success = self.save_page(prof_id, prof_name)

            if success:
                self.log['downloaded'].append(prof_id)
                return 'success'
            else:
                self.log['failed'].append(prof_id)
                return 'failed'

        except Exception as e:
            print(f"❌ Erro ao processar {prof_name}: {e}")
            self.log['failed'].append(prof_id)
            return 'failed'

    def run(self, skip_downloaded=True, start_from=None, limit=None):
        """Run the download process"""
        professors = self.get_professors()
        total = len(professors)

        print("\n" + "="*80)
        print("📚 DOWNLOAD DE CURRÍCULOS LATTES")
        print("="*80)
        print(f"Total de professores: {total}")
        print(f"Diretório de saída: {self.output_dir}")
        print(f"Pular já baixados: {skip_downloaded}")

        if start_from:
            # Find starting position
            start_idx = next((i for i, p in enumerate(professors) if p['id'] == start_from), 0)
            professors = professors[start_idx:]
            print(f"Começando de: {start_from} (posição {start_idx + 1})")

        if limit:
            professors = professors[:limit]
            print(f"Limitado a: {limit} professores")

        print("="*80)

        downloaded = 0
        skipped = 0
        failed = 0

        try:
            for idx, prof in enumerate(professors, 1):
                prof_id = prof['id']
                prof_name = prof['nome']

                print(f"\n[{idx}/{len(professors)}] Processando: {prof_name}")

                # Check if already downloaded
                if skip_downloaded and self.is_downloaded(prof_id):
                    print(f"✓ Já baixado anteriormente")
                    skipped += 1
                    continue

                # Download
                result = self.download_lattes(prof)

                if result == 'quit':
                    print("\n🛑 Interrompido pelo usuário")
                    break
                elif result == 'success':
                    downloaded += 1
                elif result == 'skip':
                    skipped += 1
                else:
                    failed += 1

                # Save progress
                self.save_log()

                # Small delay between downloads
                if idx < len(professors):
                    time.sleep(1)

        finally:
            # Cleanup
            self.driver.quit()
            self.save_log()

            # Print summary
            print("\n" + "="*80)
            print("📊 RESUMO")
            print("="*80)
            print(f"✅ Baixados com sucesso: {downloaded}")
            print(f"⏭️  Pulados: {skipped}")
            print(f"❌ Falhas: {failed}")
            print(f"📁 Arquivos salvos em: {self.output_dir}")
            print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Download sistemático de currículos Lattes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Baixar todos
  python download_lattes.py

  # Baixar apenas 5 primeiros (teste)
  python download_lattes.py --limit 5

  # Continuar de um professor específico
  python download_lattes.py --start-from andre-cavalieri

  # Forçar re-download de todos
  python download_lattes.py --no-skip
        """
    )

    parser.add_argument('--profiles-dir', type=str,
                        default='../data/professores/profiles',
                        help='Diretório com arquivos JSON dos professores')

    parser.add_argument('--output-dir', type=str,
                        default='../../lattes_data/lattes_html',
                        help='Diretório para salvar os HTMLs')

    parser.add_argument('--no-skip', action='store_true',
                        help='Não pular arquivos já baixados')

    parser.add_argument('--start-from', type=str,
                        help='ID do professor para começar (continuar)')

    parser.add_argument('--limit', type=int,
                        help='Limitar número de downloads (para teste)')

    parser.add_argument('--headless', action='store_true',
                        help='Executar navegador em modo headless (sem interface)')

    args = parser.parse_args()

    # Get script directory
    script_dir = Path(__file__).parent
    profiles_dir = (script_dir / args.profiles_dir).resolve()
    output_dir = (script_dir / args.output_dir).resolve()

    # Create downloader
    downloader = LattesDownloader(
        profiles_dir=profiles_dir,
        output_dir=output_dir,
        headless=args.headless
    )

    # Run
    downloader.run(
        skip_downloaded=not args.no_skip,
        start_from=args.start_from,
        limit=args.limit
    )


if __name__ == '__main__':
    main()
